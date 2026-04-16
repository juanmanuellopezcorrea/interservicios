from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Tuple

import pandas as pd

from conciliador_inteligente.config import MAX_COMBINACIONES, TOLERANCIA_IMPORTE


def match_multiple(movimiento: Dict, candidatos: List[Dict]) -> List[Dict]:
    """Devuelve lista de matches (posibles varios)."""
    return []


def encontrar_combo(df: pd.DataFrame, objetivo: float, tol: float = TOLERANCIA_IMPORTE) -> Optional[Tuple]:
    idx = df.index.tolist()
    max_r = max(2, int(MAX_COMBINACIONES))
    max_r = min(max_r, 10)  # guardarraíl
    for r in range(2, max_r + 1):
        for c in itertools.combinations(idx, r):
            if abs(float(df.loc[list(c)]["importe"].sum()) - float(objetivo)) <= float(tol):
                return c
    return None


def conciliar_1_a_n_pro(df1: pd.DataFrame, df2: pd.DataFrame, tol: float = TOLERANCIA_IMPORTE) -> List[Dict]:
    res: List[Dict] = []

    for i, r1 in df1.iterrows():
        if bool(r1.get("usado")):
            continue

        cand = df2[~df2["usado"]]
        combo = encontrar_combo(cand, float(r1["importe"]), tol=tol)

        if combo:
            df1.at[i, "usado"] = True
            for j in combo:
                df2.at[j, "usado"] = True

            res.append({"tipo": "1:N", "id": i, "combo": list(combo)})

    return res
