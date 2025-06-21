import streamlit as st
import pandas as pd
from io import BytesIO
import importlib.util

# Configuración inicial
st.set_page_config(page_title="Conciliación Bancaria", layout="centered")
st.title("💼 Conciliación Bancaria")

# ---- Cargar módulo externo conciliacionGPTV2.py ----
spec = importlib.util.spec_from_file_location("conciliacionGPTV2", "conciliacionGPTV2.py")
conciliacion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conciliacion)

# ---- Cargar archivo Excel ----
uploaded_file = st.file_uploader("📂 Cargar archivo Excel", type="xlsx")

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.write("📄 Hojas disponibles:", sheets)

    # ---- Selección de hojas ----
    rb_sheet = st.selectbox("🧾 Seleccioná hoja para RB", sheets)
    lb_sheet = st.selectbox("🧾 Seleccioná hoja para LB", sheets)

    if rb_sheet and lb_sheet:
        df_RB = pd.read_excel(uploaded_file, sheet_name=rb_sheet)
        df_LB = pd.read_excel(uploaded_file, sheet_name=lb_sheet)

        # ---- Selección de columnas ----
        st.subheader("🧩 Selección de columnas")
        col_rb = df_RB.columns.tolist()
        col_lb = df_LB.columns.tolist()

        debe_rb = st.selectbox("💸 Columna DEBE - RB", col_rb)
        haber_rb = st.selectbox("💰 Columna HABER - RB", col_rb)
        debe_lb = st.selectbox("💸 Columna DEBE - LB", col_lb)
        haber_lb = st.selectbox("💰 Columna HABER - LB", col_lb)

        if st.button("⚙️ Ejecutar conciliación"):
            # ---- Intentar convertir a numérico ----
            df_RB[debe_rb] = pd.to_numeric(df_RB[debe_rb], errors="coerce")
            df_RB[haber_rb] = pd.to_numeric(df_RB[haber_rb], errors="coerce")
            df_LB[debe_lb] = pd.to_numeric(df_LB[debe_lb], errors="coerce")
            df_LB[haber_lb] = pd.to_numeric(df_LB[haber_lb], errors="coerce")

            # ---- Advertencias por valores no numéricos ----
            for col, df, origen in [
                (debe_rb, df_RB, "RB - Debe"),
                (haber_rb, df_RB, "RB - Haber"),
                (debe_lb, df_LB, "LB - Debe"),
                (haber_lb, df_LB, "LB - Haber"),
            ]:
                nulos = df[col].isna().sum()
                if nulos > 0:
                    st.warning(f"⚠️ La columna '{col}' ({origen}) tiene {nulos} valores no numéricos que serán ignorados.")

            # ---- Validaciones de tipo ----
            errores = []
            if not pd.api.types.is_numeric_dtype(df_RB[debe_rb]):
                errores.append(f"La columna '{debe_rb}' de RB no es numérica.")
            if not pd.api.types.is_numeric_dtype(df_RB[haber_rb]):
                errores.append(f"La columna '{haber_rb}' de RB no es numérica.")
            if not pd.api.types.is_numeric_dtype(df_LB[debe_lb]):
                errores.append(f"La columna '{debe_lb}' de LB no es numérica.")
            if not pd.api.types.is_numeric_dtype(df_LB[haber_lb]):
                errores.append(f"La columna '{haber_lb}' de LB no es numérica.")

            if errores:
                for err in errores:
                    st.error(err)
                st.stop()

            # ---- Ejecutar conciliación si todo está OK ----
            try:
                paso1, paso2, paso3, paso4, resumen = conciliacion.run_conciliacion(
                    df_RB, df_LB, debe_rb, haber_rb, debe_lb, haber_lb
                )

                st.success("✅ Conciliación completada.")

                st.subheader("📊 Resumen")
                st.dataframe(resumen)

                # ---- Crear único archivo Excel con múltiples hojas ----
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    paso1.to_excel(writer, index=False, sheet_name="Paso1_RB_vs_LB")
                    paso2.to_excel(writer, index=False, sheet_name="Paso2_LB_vs_RB")
                    paso3.to_excel(writer, index=False, sheet_name="Paso3_RB_vs_LB")
                    paso4.to_excel(writer, index=False, sheet_name="Paso4_LB_vs_RB")
                    resumen.to_excel(writer, index=False, sheet_name="Resumen")
                output.seek(0)

                # ---- Botón de descarga del Excel completo ----
                st.download_button(
                    label="📥 Descargar Excel con todos los pasos",
                    data=output,
                    file_name="Conciliacion_Completa.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"❌ Error al ejecutar conciliación: {e}")


