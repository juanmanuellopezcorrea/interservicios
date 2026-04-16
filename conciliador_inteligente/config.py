from __future__ import annotations

import os
from dataclasses import dataclass


TOLERANCIA_IMPORTE = 0.01
UMBRAL_AUTO = 80
UMBRAL_SUGERIDO = 60
MAX_COMBINACIONES = 3
ARCHIVO_APRENDIZAJE = "data/aprendizaje.csv"


@dataclass(frozen=True)
class Settings:
    base_dir: str
    data_dir: str
    aprendizaje_csv: str


def get_settings() -> Settings:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        aprendizaje_csv=os.path.join(base_dir, ARCHIVO_APRENDIZAJE.replace("/", os.sep)),
    )
