from __future__ import annotations

import pandas as pd

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    return str(texto).lower().strip()

def normalizar_df(df):
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["importe"] = df["importe"].astype(float)
    df["descripcion"] = df["descripcion"].apply(normalizar_texto)
    if "referencia" not in df.columns:
        df["referencia"] = ""
    df["referencia"] = df["referencia"].astype(str).str.lower()
    df["usado"] = False
    return df


def normalizar_importe(v) -> float:
    """Convierte importes a float de forma robusta. Implementación pendiente."""
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return 0.0
