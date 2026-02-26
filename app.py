import streamlit as st
import pandas as pd
import sqlite3
import os
import webbrowser

# =============================
# CONFIG
# =============================

st.set_page_config(
    page_title="CRM CDA PRO",
    layout="wide"
)

st.title("🚗 CRM Renovaciones CDA")

BASES_DIR = "bases"
if not os.path.exists(BASES_DIR):
    os.makedirs(BASES_DIR)

# =============================
# FUNCIONES
# =============================

def listar_bases():
    return [f for f in os.listdir(BASES_DIR) if f.endswith(".db")]

def conectar_db(nombre):
    return sqlite3.connect(os.path.join(BASES_DIR, nombre))

# =============================
# SIDEBAR
# =============================

st.sidebar.header("📂 Bases")

archivo = st.sidebar.file_uploader("Subir Excel", type=["xlsx"])

if archivo:
    df_excel = pd.read_excel(archivo)
    nombre_db = archivo.name.replace(".xlsx", ".db")

    conn = conectar_db(nombre_db)
    df_excel.to_sql("clientes", conn, if_exists="replace", index=False)
    conn.close()

    st.sidebar.success("Base subida ✅")
    st.rerun()

bases = listar_bases()

if not bases:
    st.warning("Sube una base Excel para comenzar")
    st.stop()

base_activa = st.sidebar.selectbox("Base activa", bases)

# =============================
# CARGAR DATOS
# =============================

conn = conectar_db(base_activa)
df = pd.read_sql("SELECT * FROM clientes", conn)

# =============================
# DASHBOARD
# =============================

st.subheader("📊 Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total registros", len(df))

# =============================
# FILTROS
# =============================

st.subheader("🔎 Filtros")

busqueda = st.text_input("Buscar (placa, nombre, teléfono...)")

if busqueda:
    df = df[
        df.astype(str)
        .apply(lambda x: x.str.contains(busqueda, case=False))
        .any(axis=1)
    ]

columna_filtro = st.selectbox("Filtrar por columna", ["Ninguno"] + list(df.columns))

if columna_filtro != "Ninguno":
    valor = st.text_input("Valor filtro")
    if valor:
        df = df[df[columna_filtro].astype(str).str.contains(valor, case=False)]

st.metric("Resultados filtrados", len(df))

# =============================
# TABLA CON ACCIONES
# =============================

st.subheader("📋 Clientes")

telefono_col = st.selectbox("Columna teléfono", df.columns)
nombre_col = st.selectbox("Columna nombre", df.columns)

for i, fila in df.iterrows():

    colA, colB, colC = st.columns([4,1,1])

    with colA:
        st.write(fila.to_dict())

    numero = str(fila[telefono_col]).replace(".0","")
    nombre = str(fila[nombre_col])

    with colB:
        if st.button("📞 Llamar", key=f"call{i}"):
            webbrowser.open(f"tel:{numero}")

    with colC:
        if st.button("💬 WhatsApp", key=f"wa{i}"):

            mensaje = f"Hola {nombre}, te recordamos tu revisión técnico mecánica 🚗✅"
            mensaje = mensaje.replace(" ", "%20")

            url = f"https://wa.me/57{numero}?text={mensaje}"
            webbrowser.open(url)

# =============================
# ENVÍO MASIVO
# =============================

st.divider()
st.subheader("🚀 Envío Masivo WhatsApp")

mensaje_masivo = st.text_area(
    "Mensaje",
    "Hola {nombre}, tu revisión técnico mecánica está próxima a vencer 🚗✅ Agenda tu cita."
)

if st.button("Enviar mensajes masivos"):

    enviados = 0

    for _, fila in df.iterrows():
        numero = str(fila[telefono_col]).replace(".0","")
        nombre = str(fila[nombre_col])

        texto = mensaje_masivo.replace("{nombre}", nombre)
        texto = texto.replace(" ", "%20")

        url = f"https://wa.me/57{numero}?text={texto}"
        webbrowser.open_new_tab(url)

        enviados += 1

    st.success(f"{enviados} mensajes preparados")

conn.close()
