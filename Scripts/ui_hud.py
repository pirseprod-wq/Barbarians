# -*- coding: utf-8 -*-
"""
BP_GameHUD: интерфейс игры, рисуется в HUD (без отладочного текста):
 - окно диалога внизу (имя говорящего цветом, реплика, варианты ответа),
 - подсказка взаимодействия по центру ([E] ...),
 - уведомление о задании слева сверху,
 - загрузочный экран (чёрный фон, название места, совет).
Другие Blueprint пишут в его переменные (Dlg*, Hint*, Quest*, Loading*).
Запуск: py "D:/UOT/Barbarians/Scripts/ui_hud.py"
"""
import sys, importlib
sys.path.insert(0, "D:/UOT/Barbarians/Scripts")
import lib_build
importlib.reload(lib_build)
from lib_build import *

log = Logger("ui_hud")
CORE = "/Game/_Game/Blueprints/Core"


def build():
    bp = new_bp(CORE, "BP_GameHUD", unreal.HUD)
    T = B.get_basic_type_by_name
    lc = B.get_struct_type(unreal.LinearColor.static_struct())
    for name, typ in (("Loading", T("bool")), ("LoadingTitle", T("string")), ("LoadingTip", T("string")),
                      ("DlgSpeaker", T("string")), ("DlgText", T("string")), ("DlgColor", lc),
                      ("ChoiceText", T("string")), ("DlgUntil", T("real")),
                      ("HintText", T("string")), ("HintUntil", T("real")),
                      ("QuestText", T("string")), ("QuestUntil", T("real"))):
        B.add_member_variable(bp, name, typ)
    B.compile_blueprint(bp)
    g = G(bp)
    ev = g.event("ReceiveDrawHUD")
    # перевод размеров экрана в дробные числа
    cx = g.call(M + "Conv_IntToDouble")
    link(pin(ev, "SizeX", True), pin(cx, "InInt"))
    cy = g.call(M + "Conv_IntToDouble")
    link(pin(ev, "SizeY", True), pin(cy, "InInt"))
    W, H = pin(cx, "ReturnValue", True), pin(cy, "ReturnValue", True)

    def fx(f):
        return g.op("Multiply_DoubleDouble", W, f)

    def fy(f):
        return g.op("Multiply_DoubleDouble", H, f)

    def rect(color, alpha, x, y, w, h):
        n = g.call("/Script/Engine.HUD.DrawRect")
        pin(n, "RectColor").set_pin_value(color_str(color, alpha))
        for nm, v in (("ScreenX", x), ("ScreenY", y), ("ScreenW", w), ("ScreenH", h)):
            if isinstance(v, (int, float)):
                pin(n, nm).set_pin_value(str(v))
            else:
                link(v, pin(n, nm))
        return n

    def text(src, color, x, y, scale):
        n = g.call("/Script/Engine.HUD.DrawText")
        if isinstance(src, str):
            pin(n, "Text").set_pin_value(src)
        else:
            link(src, pin(n, "Text"))
        if isinstance(color, tuple):
            pin(n, "TextColor").set_pin_value(color_str(color))
        else:
            link(color, pin(n, "TextColor"))
        link(x, pin(n, "ScreenX"))
        link(y, pin(n, "ScreenY"))
        link(g.op("Multiply_DoubleDouble", H, scale / 1000.0 * 0.82), pin(n, "Scale"))   # 1080p -> scale*0.88
        return n

    # --- загрузочный экран
    g.row()
    br_load = g.branch(g.g("Loading"))
    link(then(ev), ex(br_load))
    r_black = rect((0, 0, 0), 1.0, 0, 0, W, H)
    t_title = text(g.g("LoadingTitle"), (0.95, 0.9, 0.8), fx(0.08), fy(0.70), 4.0)
    r_line = rect((0.6, 0.5, 0.35), 1.0, fx(0.08), fy(0.775), fx(0.3), 2)
    t_tip = text(g.g("LoadingTip"), (0.7, 0.7, 0.68), fx(0.08), fy(0.80), 2.2)
    t_wait = text("Загрузка...", (0.5, 0.5, 0.5), fx(0.86), fy(0.93), 1.8)
    link(then(br_load), ex(r_black))
    chain([r_black, t_title, r_line, t_tip, t_wait])

    # --- диалог
    g.row()
    br_dlg = g.branch(g.op("Less_DoubleDouble", g.now(), g.g("DlgUntil")))
    link(B.find_else_pin(br_load), ex(br_dlg))
    box = rect((0.02, 0.018, 0.015), 0.8, fx(0.14), fy(0.73), fx(0.72), fy(0.21))
    edge = rect((0.6, 0.5, 0.35), 0.9, fx(0.14), fy(0.73), fx(0.72), 2)
    t_name = text(g.g("DlgSpeaker"), g.g("DlgColor"), fx(0.16), fy(0.745), 2.6)
    t_line = text(g.g("DlgText"), (0.93, 0.91, 0.86), fx(0.16), fy(0.79), 2.2)
    t_choice = text(g.g("ChoiceText"), (1.0, 0.9, 0.45), fx(0.16), fy(0.885), 2.2)
    link(then(br_dlg), ex(box))
    after_dlg = chain([box, edge, t_name, t_line, t_choice])

    # --- подсказка
    g.row()
    br_hint = g.branch(g.op("Less_DoubleDouble", g.now(), g.g("HintUntil")))
    for o in after_dlg + [B.find_else_pin(br_dlg)]:
        link(o, ex(br_hint))
    t_hint = text(g.g("HintText"), (0.95, 0.95, 0.95), fx(0.44), fy(0.6), 2.3)
    link(then(br_hint), ex(t_hint))

    # --- задание
    g.row()
    br_q = g.branch(g.op("Less_DoubleDouble", g.now(), g.g("QuestUntil")))
    link(then(t_hint), ex(br_q))
    link(B.find_else_pin(br_hint), ex(br_q))
    q_bg = rect((0, 0, 0), 0.55, fx(0.02), fy(0.03), fx(0.6), fy(0.14))
    q_t = text(g.g("QuestText"), (1.0, 0.78, 0.3), fx(0.03), fy(0.045), 2.0)
    link(then(br_q), ex(q_bg))
    chain([q_bg, q_t])

    B.compile_blueprint(bp)
    errs = g.ed.list_nodes_with_errors()
    log("ошибки: %s" % [n.get_name() for n in errs] if errs else "скомпилирован без ошибок")
    eal.save_loaded_asset(bp)
    # подключить к режиму игры
    gm_path = CORE + "/BP_VillageGameMode"
    if eal.does_asset_exist(gm_path):
        gm = unreal.load_asset(gm_path)
        cdo = unreal.get_default_object(gm.generated_class())
        cdo.modify()
        cdo.set_editor_property("hud_class", bp.generated_class())
        gm.modify()
        eal.save_loaded_asset(gm, False)
        log("hud_class сейчас: %s" % cdo.get_editor_property("hud_class"))
        log("HUD подключён к BP_VillageGameMode")
    return bp


try:
    build()
    log("готово")
except Exception as e:
    import traceback
    log("ОШИБКА: %s\n%s" % (e, traceback.format_exc()))
    raise
