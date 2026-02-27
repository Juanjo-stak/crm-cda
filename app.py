import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import plotly.express as px

# ======================================================
# CONFIGURACIÓN
# ======================================================

st.set_page_config(page_title="CRM CDA", layout="wide")

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_BASES = "bases"

os.makedirs(CARPETA_BASES, exist_ok=True)

# ======================================================
# USUARIOS
# ======================================================

def inicializar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS) or os.path.getsize(ARCHIVO_USUARIOS) == 0:
        with open(ARCHIVO_USUARIOS, "w") as f:
            json.dump({
                "admin": {
                    "password": "admin123",
                    "rol": "admin"
                }
            }, f, indent=4)

def cargar_usuarios():
    with open(ARCHIVO_USUARIOS, "r") as f:
        return json.load(f)

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(data, f, indent=4)

inicializar_usuarios()

# ======================================================
# SESSION
# ======================================================

if "login" not in st.session_state:
    st.session_state.login = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None

# ======================================================
# LOGIN
# ======================================================

def pantalla_login():
    st.title("🔐 CRM CDA")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        usuarios = cargar_usuarios()

        if user in usuarios and usuarios[user]["password"] == pwd:
            st.session_state.login = True
            st.session_state.usuario = user
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.login:
    pantalla_login()
    st.stop()

# ======================================================
# HEADER
# ======================================================

usuario_actual = st.session_state.usuario
rol_actual = st.session_state.rol

st.title("  Renovaciones ")
st.write(f"👤 Usuario: {usuario_actual} | Rol: {rol_actual}")

col_logout1, col_logout2 = st.columns([6,1])

with col_logout2:
    if st.button("🚪 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

# ======================================================
# CARPETA USUARIO
# ======================================================

carpeta_usuario = os.path.join(CARPETA_BASES, usuario_actual)
os.makedirs(carpeta_usuario, exist_ok=True)

# ======================================================
# TABS
# ======================================================

tabs_lista = ["📊 CRM"]
if rol_actual == "admin":
    tabs_lista.append("👑 Panel Administración")
    tabs_lista.append("📈 Dashboard Visual")

tabs_objs = st.tabs(tabs_lista)

tab_crm = tabs_objs[0]
if rol_actual == "admin":
    tab_admin = tabs_objs[1]
    tab_dashboard = tabs_objs[2]

# ======================================================
# ====================== CRM ===========================
# ======================================================

with tab_crm:

    st.sidebar.header("📂 Bases de Datos")

    archivo_subido = st.sidebar.file_uploader("Subir base Excel", type=["xlsx"])

    if archivo_subido:
        ruta_guardado = os.path.join(carpeta_usuario, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("Base guardada correctamente")
        st.rerun()

    bases_disponibles = []

    if rol_actual == "admin":
        for usuario in os.listdir(CARPETA_BASES):
            ruta_user = os.path.join(CARPETA_BASES, usuario)
            if not os.path.isdir(ruta_user):
                continue
            for archivo in os.listdir(ruta_user):
                ruta_archivo = os.path.join(ruta_user, archivo)
                if os.path.isfile(ruta_archivo) and archivo.endswith(".xlsx"):
                    bases_disponibles.append((f"{usuario} - {archivo}", ruta_archivo))
    else:
        for archivo in os.listdir(carpeta_usuario):
            ruta_archivo = os.path.join(carpeta_usuario, archivo)
            if os.path.isfile(ruta_archivo) and archivo.endswith(".xlsx"):
                bases_disponibles.append((archivo, ruta_archivo))

    if not bases_disponibles:
        st.warning("No hay bases cargadas")
        st.stop()

    nombres = [x[0] for x in bases_disponibles]
    seleccion = st.sidebar.selectbox("Seleccionar base", nombres)
    ARCHIVO = dict(bases_disponibles)[seleccion]

    df = pd.read_excel(ARCHIVO)
    df.columns = df.columns.str.strip()

    columnas_lower = {col.lower(): col for col in df.columns}
    posibles_fechas = ["fecha_renovacion","fecha","vencimiento","fecha vencimiento"]

    columna_fecha = None
    for posible in posibles_fechas:
        if posible in columnas_lower:
            columna_fecha = columnas_lower[posible]
            break

    if columna_fecha is None:
        st.error("No se encontró columna de fecha")
        st.stop()

    df.rename(columns={columna_fecha: "Fecha_Renovacion"}, inplace=True)

    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

# ======================================================
# DASHBOARD VISUAL SOLO ADMIN
# ======================================================

if rol_actual == "admin":

    with tab_dashboard:

        st.header("📈 Dashboard Visual de Estados")

        if 'df' in locals():

            st.subheader("📊 Métricas Generales")

            total = len(df)
            pendientes = (df["Estado"]=="Pendiente").sum()
            agendados = (df["Estado"]=="Agendado").sum()
            renovados = (df["Estado"]=="Renovado").sum()

            st.metric("Total", total)
            st.metric("Pendientes", pendientes)
            st.metric("Agendados", agendados)
            st.metric("Renovados", renovados)

            st.divider()

            conteo_estados = df["Estado"].value_counts().reindex(
                ["Pendiente","Agendado","Renovado"], fill_value=0
            )

            fig_bar = px.bar(
                x=conteo_estados.index,
                y=conteo_estados.values,
                text=conteo_estados.values
            )

            st.plotly_chart(fig_bar)

            fig_pie = px.pie(
                names=conteo_estados.index,
                values=conteo_estados.values
            )

            st.plotly_chart(fig_pie)
