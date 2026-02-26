import streamlit as st
import pandas as pd
import sqlite3
import os
import webbrowser

# =============================
# CONFIGURACIÓN GENERAL
# =============================

st.set_page_config(
    page_title="CRM CDA Renovaciones",
    layout="wide"
)

st.title("🚗 CRM Renovaciones CDA")

# =============================
# CARPETA DONDE SE GUARDAN BASES
# =============================

BASES_DIR = "bases"

if not os.path.exists(BASES_DIR):
    os.makedirs(BASES_DIR)

# =============================
# FUNCIONES
# =============================

def listar_bases():
    """Lista solo bases subidas por el usuario"""
    archivos = os.listdir(BASES_DIR)
    return [f for f in archivos if f.endswith(".db")]

def conectar_db(nombre):
    ruta = os.path.join(BASES_DIR, nombre)
    return sqlite3.connect(ruta)

# =============================
# SIDEBAR - SUBIR BASE
# =============================

st.sidebar.header("📂 Bases de Datos")

archivo = st.sidebar.file_uploader(
    "Subir base Excel",
    type=["xlsx"]
)

if archivo is not None:

    df_excel = pd.read_excel(archivo)

    nombre_db = archivo.name.replace(".xlsx", ".db")
    ruta_db = os.path.join(BASES_DIR, nombre_db)

    conn = sqlite3.connect(ruta_db)
    df_excel.to_sql("clientes", conn, if_exists="replace", index=False)
    conn.close()

    st.sidebar.success("✅ Base subida correctamente")
    st.rerun()

# =============================
# MOSTRAR SOLO BASES SUBIDAS
# =============================

bases = listar_bases()

if len(bases) == 0:
    st.warning("⚠️ No hay bases cargadas. Sube un archivo Excel para comenzar.")
    st.stop()

base_activa = st.sidebar.selectbox(
    "Seleccionar base activa",
    bases
)

# =============================
# CARGAR DATOS
# =============================

conn = conectar_db(base_activa)

try:
    df = pd.read_sql("SELECT * FROM clientes", conn)
except:
    st.error("❌ La base no contiene tabla válida.")
    st.stop()

# =============================
# FILTRO BUSCADOR
# =============================

st.subheader("🔎 Buscar cliente")

busqueda = st.text_input("Buscar por cualquier dato (placa, nombre, etc)")

if busqueda:
    df = df[
        df.astype(str)
        .apply(lambda x: x.str.contains(busqueda, case=False))
        .any(axis=1)
    ]

st.dataframe(df, use_container_width=True)

# =============================
# ENVÍO MASIVO WHATSAPP BUSINESS
# =============================

st.divider()
st.subheader("📲 Envío Masivo WhatsApp Business")

col_numero = st.selectbox(
    "Columna que contiene teléfonos",
    df.columns
)

col_nombre = st.selectbox(
    "Columna que contiene nombres",
    df.columns
)

mensaje = st.text_area(
    "Mensaje a enviar",
    "Hola {nombre}, te recordamos que tu revisión técnico mecánica está próxima a vencer 🚗✅ Agenda tu cita hoy mismo."
)

if st.button("🚀 Iniciar envío masivo"):

    enviados = 0

    for _, fila in df.iterrows():

        numero = str(fila[col_numero]).replace(".0","")
        nombre = str(fila[col_nombre])

        texto = mensaje.replace("{nombre}", nombre)
        texto = texto.replace(" ", "%20")

        url = f"https://wa.me/57{numero}?text={texto}"

        webbrowser.open_new_tab(url)
        enviados += 1

    st.success(f"✅ Mensajes preparados: {enviados}")

conn.close()
