from __future__ import annotations

import re
from typing import List

import pandas as pd
import pdfplumber

def leer_pdf_tablas(ruta: str) -> pd.DataFrame:
    datos = []
    with pdfplumber.open(ruta) as pdf:
        for p in pdf.pages:
            tablas = p.extract_tables()
            for t in tablas:
                for fila in t[1:]:
                    datos.append(fila)
    return pd.DataFrame(datos)


def extraer_texto(ruta: str) -> str:
    texto = ""
    with pdfplumber.open(ruta) as pdf:
        for p in pdf.pages:
            texto += p.extract_text() or ""
    return texto


def parsear(texto: str) -> pd.DataFrame:
    datos = []
    for linea in texto.split("\n"):
        m = re.search(r"(\d{2}/\d{2}/\d{4}).*?(-?\d+,\d{2})", linea)
        if m:
            datos.append(
                {
                    "fecha": m.group(1),
                    "importe": float(m.group(2).replace(",", ".")),
                    "descripcion": linea,
                    "referencia": "",
                }
            )
    return pd.DataFrame(datos)


def procesar_pdf(ruta: str) -> pd.DataFrame:
    df = leer_pdf_tablas(ruta)
    if len(df) > 0:
        df.columns = ["fecha", "descripcion", "importe", "referencia"][: len(df.columns)]
        return df

    texto = extraer_texto(ruta)
    df = parsear(texto)

    return df


# Alias de compatibilidad con la estructura inicial del paquete
def extraer_texto_pdf(ruta_pdf: str) -> str:
    return extraer_texto(ruta_pdf)


def extraer_tablas_pdf(ruta_pdf: str) -> List[dict]:
    df = leer_pdf_tablas(ruta_pdf)
    if df is None or len(df) == 0:
        return []
    return df.to_dict(orient="records")
