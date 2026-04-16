from __future__ import annotations

import argparse
import os

from conciliador_inteligente.config import get_settings
from conciliador_inteligente.modules.export import exportar
from conciliador_inteligente.modules.matching import conciliar
from conciliador_inteligente.modules.matching_multiple import conciliar_1_a_n_pro
from conciliador_inteligente.modules.normalizacion import normalizar_df
from conciliador_inteligente.modules.pdf import procesar_pdf
from conciliador_inteligente.modules.scoring_ml import entrenar_modelo


def _cargar_entrada(ruta: str):
    """
    Carga una entrada desde PDF o Excel y devuelve un DataFrame con columnas
    compatibles con normalizar_df: fecha, importe, descripcion, (opcional) referencia.
    """
    ext = os.path.splitext((ruta or "").lower())[1]
    if ext in (".xlsx", ".xls"):
        import pandas as pd

        df = pd.read_excel(ruta)
        # Normalizaciones básicas de nombres de columnas típicos
        cols = {c: str(c).strip().lower() for c in df.columns}
        inv = {v: k for k, v in cols.items()}

        def _pick(*names: str):
            for n in names:
                if n in inv:
                    return inv[n]
            return None

        fecha_col = _pick("fecha", "date", "f. valor", "valor", "fecha valor")
        importe_col = _pick("importe", "amount", "importe (€)", "importe eur", "euros", "debe", "haber")
        desc_col = _pick("descripcion", "concepto", "detalle", "descripcion movimiento", "descripción", "description")
        ref_col = _pick("referencia", "ref", "referencia/num", "nº", "numero", "número", "num", "documento", "doc")

        # Si no encontramos columnas, dejamos que falle con un error claro
        if fecha_col is None or importe_col is None or desc_col is None:
            faltan = []
            if fecha_col is None:
                faltan.append("fecha")
            if importe_col is None:
                faltan.append("importe")
            if desc_col is None:
                faltan.append("descripcion")
            raise ValueError(
                "Excel inválido: faltan columnas obligatorias "
                + ", ".join(faltan)
                + ". Debe contener al menos: fecha, importe, descripcion."
            )

        out = df.rename(
            columns={
                fecha_col: "fecha",
                importe_col: "importe",
                desc_col: "descripcion",
                **({ref_col: "referencia"} if ref_col else {}),
            }
        )
        # Solo columnas relevantes
        keep = ["fecha", "importe", "descripcion"] + (["referencia"] if "referencia" in out.columns else [])
        return out[keep]

    # Por defecto, PDF
    return procesar_pdf(ruta)


def ejecutar(facturas: str, banco: str, *, output_dir: str | None = None):
    df1 = normalizar_df(_cargar_entrada(facturas))
    df2 = normalizar_df(_cargar_entrada(banco))

    modelo = entrenar_modelo()

    r1 = conciliar(df1, df2, modelo)
    r2 = conciliar_1_a_n_pro(df1, df2)

    fact_xlsx, banco_xlsx = exportar(df1, df2, output_dir=output_dir)

    return r1, r2, fact_xlsx, banco_xlsx


def main() -> int:
    p = argparse.ArgumentParser(description="Conciliador inteligente (CLI)")
    p.add_argument("--facturas", help="Ruta PDF de facturas", required=False)
    p.add_argument("--banco", help="Ruta PDF extracto banco", required=False)
    args = p.parse_args()

    s = get_settings()
    print("conciliador_inteligente listo")
    print("aprendizaje_csv:", s.aprendizaje_csv)

    if args.facturas and args.banco:
        ejecutar(args.facturas, args.banco)
        print("Exportados: facturas_resultado.xlsx, banco_resultado.xlsx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
