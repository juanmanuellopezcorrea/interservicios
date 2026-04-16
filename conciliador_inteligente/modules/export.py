from __future__ import annotations

import os
from typing import List

import pandas as pd

def exportar_resultados_csv(ruta_salida: str, filas: List[dict]) -> None:
    """Exporta resultados a CSV. Implementación pendiente."""
    raise NotImplementedError("Pendiente: exportar_resultados_csv")


def exportar(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    output_dir: str | None = None,
    facturas_filename: str = "facturas_resultado.xlsx",
    banco_filename: str = "banco_resultado.xlsx",
) -> tuple[str, str]:
    """
    Exporta los DataFrames a Excel y devuelve las rutas de salida.

    Mantiene compatibilidad con el comportamiento anterior (mismos nombres por defecto).
    """
    base = output_dir or os.getcwd()
    os.makedirs(base, exist_ok=True)
    fact_path = os.path.join(base, facturas_filename)
    banco_path = os.path.join(base, banco_filename)
    df1.to_excel(fact_path, index=False)
    df2.to_excel(banco_path, index=False)
    return fact_path, banco_path
