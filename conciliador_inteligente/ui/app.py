from __future__ import annotations

import os
import tempfile

import streamlit as st

from conciliador_inteligente.main import ejecutar

def main() -> None:
    st.set_page_config(page_title="Conciliador inteligente", layout="wide")
    st.title("Conciliador Inteligente")

    f = st.file_uploader("Facturas (PDF)", type=["pdf"])
    b = st.file_uploader("Banco (PDF)", type=["pdf"])

    if st.button("Conciliar", type="primary", disabled=not (f and b)):
        with st.spinner("Conciliando..."):
            tmp_dir = tempfile.mkdtemp(prefix="conciliador_")

            fact_path = os.path.join(tmp_dir, f"facturas_{f.name}")
            banco_path = os.path.join(tmp_dir, f"banco_{b.name}")

            with open(fact_path, "wb") as wf:
                wf.write(f.getbuffer())
            with open(banco_path, "wb") as wb:
                wb.write(b.getbuffer())

            r1, r2 = ejecutar(fact_path, banco_path)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Conciliación 1:1")
            st.write(r1)
        with c2:
            st.subheader("Conciliación 1:N")
            st.write(r2)

        st.info("Se han exportado los Excel en el directorio de ejecución: facturas_resultado.xlsx y banco_resultado.xlsx")


if __name__ == "__main__":
    main()

