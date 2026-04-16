from __future__ import annotations

import os
from typing import Dict, Optional

import pandas as pd
from rapidfuzz import fuzz
from sklearn.linear_model import LogisticRegression

from conciliador_inteligente.config import ARCHIVO_APRENDIZAJE


def extraer_features(r1: Dict, r2: Dict) -> Dict[str, float]:
    return {
        "importe_diff": abs(float(r1.get("importe", 0) or 0) - float(r2.get("importe", 0) or 0)),
        "dias_diff": abs((r1["fecha"] - r2["fecha"]).days) if pd.notna(r1.get("fecha")) and pd.notna(r2.get("fecha")) else 999,
        "fuzzy_desc": float(fuzz.token_sort_ratio(str(r1.get("descripcion", "")), str(r2.get("descripcion", "")))),
        "referencia_match": float(int(str(r1.get("referencia", "")) == str(r2.get("referencia", "")))),
    }


def entrenar_modelo(path: str = ARCHIVO_APRENDIZAJE) -> Optional[LogisticRegression]:
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    if len(df) < 10:
        return None
    if "match" not in df.columns:
        return None

    X = df.drop(columns=["match"])
    y = df["match"]

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    return model


def guardar_decision(features: Dict[str, float], match: int, path: str = ARCHIVO_APRENDIZAJE) -> None:
    df = pd.DataFrame([{**features, "match": int(match)}])
    if os.path.exists(path):
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)


def puntuar_match(movimiento: Dict, candidato: Dict, model: Optional[LogisticRegression] = None) -> float:
    """Devuelve score 0..1 para un match (ML si hay modelo, si no 0.0)."""
    if model is None:
        model = entrenar_modelo()
    if model is None:
        return 0.0
    feats = extraer_features(movimiento, candidato)
    X = pd.DataFrame([feats])
    try:
        proba = float(model.predict_proba(X)[0][1])
        return max(0.0, min(1.0, proba))
    except Exception:
        return 0.0
