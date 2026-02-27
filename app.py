import streamlit as st
import pandas as pd
import datetime
import urllib.parse
from io import BytesIO

# ==================================================
# CONFIGURACIÓN INICIAL
# ==================================================

st.set_page_config(page_title="CRM Técnico-Mecánica", layout="wide")

st.title("🚗 CRM - Técnico Mecánica")

# ==================================================
# ARCHIVO BASE
# ==================================================

FILE_NAME = "clientes_tecnomecanica.xlsx"

def cargar_datos():
    try:
        df = pd.read_excel(FILE_NAME)
    except:
        df = pd.DataFrame(columns=[
            "Cliente",
            "Telefono",
            "Placa",
            "Fecha_Renovacion",
            "Estado"
        ])
    return df

def guardar_datos(df):
    df.to_excel(FILE_NAME, index=False)

df = cargar_datos()

# ==================================================
# TABS PRINCIPALES
# ==================================================

tab_dashboard, tab_crm, tab_admin = st.tabs(["📊 Dashboard", "📋 CRM", "⚙️ Admin"])
# ==================================================
# DASHBOARD
# ==================================================

with tab_dashboard:

    st.subheader("📊 Métricas Generales")

    hoy = datetime.date.today()

    if not df.empty:
        df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha_Renovacion"], errors="coerce")
        df["Dias_Restantes"] = (df["Fecha_Renovacion"].dt.date - hoy).dt.days

        total_clientes = len(df)
        pendientes = df[df["Estado"] == "Pendiente"].shape[0]
        vencidos = df[df["Dias_Restantes"] < 0].shape[0]
        proximos = df[(df["Dias_Restantes"] >= 0) & (df["Dias_Restantes"] <= 30)].shape[0]

        # MÉTRICAS EN VERTICAL (como pediste)
        st.metric("👥 Total Clientes", total_clientes)
        st.metric("⏳ Pendientes", pendientes)
        st.metric("⚠️ Vencidos", vencidos)
        st.metric("📅 Próximos 30 días", proximos)

        st.divider()

        st.subheader("📋 Tabla General")
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No hay datos registrados aún.")
        # ==================================================
# CRM
# ==================================================

with tab_crm:

    st.subheader("📋 Gestión de Clientes")

    if not df.empty:
        df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha_Renovacion"], errors="coerce")

        filtro_estado = st.selectbox(
            "Filtrar por Estado",
            ["Todos"] + list(df["Estado"].dropna().unique())
        )

        if filtro_estado != "Todos":
            df_filtrado = df[df["Estado"] == filtro_estado]
        else:
            df_filtrado = df.copy()

        st.dataframe(df_filtrado, use_container_width=True)

    else:
        df_filtrado = pd.DataFrame()
        st.info("No hay clientes registrados.")

    st.divider()

    # ==================================================
    # 📢 ENVÍO MASIVO WHATSAPP (AGREGADO)
    # ==================================================

    st.markdown("## 📢 Envío Masivo por WhatsApp")

    if st.button("🚀 Generar Envío Masivo"):

        enviados = 0

        for i, row in df_filtrado.iterrows():

            if "Telefono" in df.columns and not pd.isna(row.get("Telefono", "")):

                telefono = str(row.get("Telefono", "")).replace(".0", "").replace(" ", "").replace("-", "")

                if not telefono.startswith("57"):
                    telefono = "57" + telefono

                fecha_texto = row["Fecha_Renovacion"].strftime("%d/%m/%Y") if not pd.isna(row["Fecha_Renovacion"]) else ""

                mensaje = f"""Hola {row.get('Cliente','')}, soy Juan José 👋

Tu vehículo con placa {row.get('Placa','')} vence el {fecha_texto}.

¿Deseas agendar tu revisión? 🚗✅"""

                mensaje = urllib.parse.quote(mensaje)

                url = f"https://wa.me/{telefono}?text={mensaje}"

                st.markdown(
                    f'<a href="{url}" target="_blank">Enviar a {row.get("Cliente","")}</a>',
                    unsafe_allow_html=True
                )

                enviados += 1

        if enviados == 0:
            st.warning("No hay contactos con teléfono en el filtro actual.")
        else:
            st.success(f"Se generaron {enviados} enlaces de envío.")

    st.divider()

    # ==================================================
    # WHATSAPP INDIVIDUAL
    # ==================================================

    if not df_filtrado.empty:
        st.markdown("### 📲 Contacto rápido")

        cliente_sel = st.selectbox("Seleccionar Cliente", df_filtrado["Cliente"])

        cliente_data = df_filtrado[df_filtrado["Cliente"] == cliente_sel].iloc[0]

        telefono = str(cliente_data["Telefono"]).replace(".0", "").replace(" ", "").replace("-", "")

        if not telefono.startswith("57"):
            telefono = "57" + telefono

        fecha_texto = cliente_data["Fecha_Renovacion"].strftime("%d/%m/%Y") if not pd.isna(cliente_data["Fecha_Renovacion"]) else ""

        mensaje = f"""Hola {cliente_sel}, soy Juan José 👋

Tu vehículo con placa {cliente_data['Placa']} vence el {fecha_texto}.

¿Deseas agendar tu revisión? 🚗✅"""

        mensaje = urllib.parse.quote(mensaje)

        url = f"https://wa.me/{telefono}?text={mensaje}"

        st.markdown(
            f'<a href="{url}" target="_blank">📲 Enviar WhatsApp</a>',
            unsafe_allow_html=True
        )
        # ==================================================
# ADMIN
# ==================================================

with tab_admin:

    st.subheader("⚙️ Administración")

    with st.form("form_cliente"):

        cliente = st.text_input("Nombre del Cliente")
        telefono = st.text_input("Teléfono")
        placa = st.text_input("Placa del Vehículo")
        fecha = st.date_input("Fecha de Renovación")
        estado = st.selectbox("Estado", ["Pendiente", "Contactado", "Renovado"])

        submitted = st.form_submit_button("💾 Guardar Cliente")

        if submitted:

            nuevo = pd.DataFrame([{
                "Cliente": cliente,
                "Telefono": telefono,
                "Placa": placa,
                "Fecha_Renovacion": fecha,
                "Estado": estado
            }])

            df = pd.concat([df, nuevo], ignore_index=True)
            guardar_datos(df)

            st.success("Cliente guardado correctamente ✅")

    st.divider()

    if not df.empty:

        st.subheader("🗑️ Eliminar Cliente")

        cliente_eliminar = st.selectbox("Seleccionar Cliente a eliminar", df["Cliente"])

        if st.button("❌ Eliminar"):

            df = df[df["Cliente"] != cliente_eliminar]
            guardar_datos(df)

            st.success("Cliente eliminado correctamente ✅")
            st.experimental_rerun()
