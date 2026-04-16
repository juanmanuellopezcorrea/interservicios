from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from conciliador_inteligente.config import TOLERANCIA_IMPORTE, UMBRAL_AUTO
from conciliador_inteligente.modules.scoring_ml import extraer_features


def match_unico(movimiento: Dict, candidatos: List[Dict]) -> Dict | None:
    """Devuelve el mejor candidato (o None)."""
    if not candidatos:
        return None
    best = None
    best_score = -1.0
    for c in candidatos:
        try:
            score = calcular_score(movimiento, c, modelo=None)
        except Exception:
            score = 0.0
        if score > best_score:
            best_score = score
            best = c
    return best


def calcular_score(r1, r2, modelo=None) -> float:
    """
    Score 0..100.
    - Si hay modelo (sklearn), usa probabilidad * 100
    - Si no, usa reglas simples (importe + referencia)
    """
    if modelo is not None:
        X = pd.DataFrame([extraer_features(r1, r2)])
        return float(modelo.predict_proba(X)[0][1] * 100)

    score = 0.0
    try:
        if abs(float(r1["importe"]) - float(r2["importe"])) < float(TOLERANCIA_IMPORTE):
            score += 50.0
    except Exception:
        pass
    try:
        ref1 = str(r1.get("referencia", "") or "")
        ref2 = str(r2.get("referencia", "") or "")
        if ref1 and ref1 == ref2:
            score += 40.0
    except Exception:
        pass
    return score


def conciliar(df1: pd.DataFrame, df2: pd.DataFrame, modelo=None) -> List[Dict]:
    resultados: List[Dict] = []

    for i, r1 in df1.iterrows():
        best_score = 0.0
        best_j: Optional[int] = None

        for j, r2 in df2.iterrows():
            if bool(r2.get("usado")):
                continue

            score = calcular_score(r1, r2, modelo)

            if score > best_score:
                best_score = score
                best_j = j

        if best_score >= float(UMBRAL_AUTO):
            df1.at[i, "usado"] = True
            if best_j is not None:
                df2.at[best_j, "usado"] = True
            estado = "conciliado"
        else:
            estado = "pendiente"

        resultados.append({"id1": i, "id2": best_j, "score": float(best_score), "estado": estado})

    return resultados
