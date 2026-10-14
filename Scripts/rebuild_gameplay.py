# -*- coding: utf-8 -*-
"""Пересобрать погоду, интерфейс и дом Бранда (без перестройки села и леса)."""
import os
here = "D:/UOT/Barbarians/Scripts"
for f in ("weather_rain.py", "ui_hud.py", "brand_house.py"):
    exec(open(os.path.join(here, f), encoding="utf-8").read(), {"__name__": "__main__"})
