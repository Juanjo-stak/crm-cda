import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import plotly.express as px  # Para gráficos interactivos

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

# ======================================================
# 🔴 AGREGADO: CERRAR SESIÓN
# ======================================================

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
# =========================
# KPI PROFESIONAL VERTICAL
# =========================

st.subheader("📊 Métricas Generales")

total = len(df)
pendientes = (df["Estado"]=="Pendiente").sum()
agendados = (df["Estado"]=="Agendado").sum()
renovados = (df["Estado"]=="Renovado").sum()

st.markdown(f"""
<div style="
    background-color:#1f2937;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Total Registros</h3>
    <h1 style="font-size:40px;">{total}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#7f1d1d;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Pendientes</h3>
    <h1 style="font-size:40px;">{pendientes}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#92400e;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Agendados</h3>
    <h1 style="font-size:40px;">{agendados}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#065f46;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Renovados</h3>
    <h1 style="font-size:40px;">{renovados}</h1>
</div>
""", unsafe_allow_html=True)

st.divider()

# ======================================================
# TABS
# ======================================================

tabs_lista = ["📊 CRM"]
if rol_actual == "admin":
    tabs_lista.append("👑 Panel Administración")
    tabs_lista.append("📈 Dashboard Visual")  # Nueva pestaña

tabs_objs = st.tabs(tabs_lista)

# Asignar objetos a variables según rol
tab_crm = tabs_objs[0]
if rol_actual == "admin":import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import plotly.express as px  # Para gráficos interactivos

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

# ======================================================
# CERRAR SESIÓN
# ======================================================

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

    st.sidebar.divider()
    st.sidebar.subheader("🗑 Eliminar Base de Datos")

    if st.sidebar.button("Eliminar base seleccionada"):
        try:
            os.remove(ARCHIVO)
            st.sidebar.success("Base eliminada correctamente")
            st.rerun()
        except Exception:
            st.sidebar.error("Error al eliminar la base")

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
        st.write("Columnas detectadas:", list(df.columns))
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

    # ==================================================
    # FILTROS
    # ==================================================

    st.markdown("## 🔎 Filtros")

    col_f1, col_f2, col_f3 = st.columns(3)

    if "Sede" not in df.columns:
        df["Sede"] = "Sin sede"

    fecha_min = df["Fecha_Renovacion"].min()
    fecha_max = df["Fecha_Renovacion"].max()

    with col_f1:
        fecha_inicio = st.date_input("Desde", fecha_min.date())

    with col_f2:
        fecha_fin = st.date_input("Hasta", fecha_max.date())

    with col_f3:
        sedes = ["Todas"] + sorted(df["Sede"].dropna().astype(str).unique().tolist())
        sede_sel = st.selectbox("Sede", sedes)

    df_filtrado = df[
        (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
        (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
    ]

    if sede_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

    st.divider()

    # (resto del CRM queda exactamente igual…)
