import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(page_title="CRM CDA", layout="wide")

DATA_DIR = "data"
USERS_FILE = "users.json"

os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================================
# FUNCIONES USUARIOS
# ==========================================================

def cargar_usuarios():
    if not os.path.exists(USERS_FILE):
        usuarios_default = {
            "admin": {"password": "admin123", "rol": "admin"}
        }
        with open(USERS_FILE, "w") as f:
            json.dump(usuarios_default, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(USERS_FILE, "w") as f:
        json.dump(usuarios, f)

usuarios = cargar_usuarios()

# ==========================================================
# LOGIN
# ==========================================================

if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None

if st.session_state.usuario is None:
    st.title("🔐 Login CRM CDA")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == password:
            st.session_state.usuario = user
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.write(f"👤 Usuario: {st.session_state.usuario}")
st.sidebar.write(f"🔑 Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.rerun()

# ==========================================================
# ADMIN - CREAR / ELIMINAR USUARIOS
# ==========================================================

if st.session_state.rol == "admin":
    st.sidebar.markdown("## 👥 Gestión Usuarios")

    nuevo_user = st.sidebar.text_input("Nuevo usuario")
    nuevo_pass = st.sidebar.text_input("Contraseña", type="password")
    rol = st.sidebar.selectbox("Rol", ["usuario", "admin"])

    if st.sidebar.button("Crear usuario"):
        if nuevo_user not in usuarios:
            usuarios[nuevo_user] = {"password": nuevo_pass, "rol": rol}
            guardar_usuarios(usuarios)
            os.makedirs(os.path.join(DATA_DIR, nuevo_user), exist_ok=True)
            st.sidebar.success("Usuario creado")
        else:
            st.sidebar.error("Usuario ya existe")

    eliminar = st.sidebar.selectbox("Eliminar usuario", [""] + list(usuarios.keys()))
    if st.sidebar.button("Eliminar usuario") and eliminar:
        if eliminar != "admin":
            usuarios.pop(eliminar)
            guardar_usuarios(usuarios)
            st.sidebar.success("Usuario eliminado")
        else:
            st.sidebar.error("No puedes eliminar admin")

# ==========================================================
# CARPETAS
# ==========================================================

if st.session_state.rol == "admin":
    carpetas = [os.path.join(DATA_DIR, d) for d in os.listdir(DATA_DIR)]
else:
    user_path = os.path.join(DATA_DIR, st.session_state.usuario)
    os.makedirs(user_path, exist_ok=True)
    carpetas = [user_path]

archivos = []
for carpeta in carpetas:
    if os.path.isdir(carpeta):
        for f in os.listdir(carpeta):
            if f.endswith(".csv"):
                archivos.append(os.path.join(carpeta, f))

# ==========================================================
# SUBIR ARCHIVO
# ==========================================================

st.sidebar.markdown("## 📂 Subir Base")

uploaded_file = st.sidebar.file_uploader("Subir CSV", type=["csv"])

if uploaded_file:
    ruta_user = os.path.join(DATA_DIR, st.session_state.usuario)
    os.makedirs(ruta_user, exist_ok=True)

    ruta_guardado = os.path.join(ruta_user, uploaded_file.name)
    with open(ruta_guardado, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.sidebar.success("Archivo subido")
    st.rerun()

if not archivos:
    st.warning("No hay bases disponibles")
    st.stop()

archivo_actual = st.selectbox("Seleccionar base", archivos)

# ==========================================================
# FUNCIONES DATOS
# ==========================================================

def cargar_datos(archivo):
    df = pd.read_csv(archivo)

    columnas_necesarias = ["Cliente", "Telefono", "Placa", "Sede", "Fecha_Renovacion", "Estado"]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = ""

    df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha_Renovacion"], errors="coerce")
    df["Estado"] = df["Estado"].replace("", "Pendiente")

    return df

def guardar_datos(df, archivo):
    df.to_csv(archivo, index=False)

# ==========================================================
# SESSION DATAFRAME
# ==========================================================

if "df_actual" not in st.session_state:
    st.session_state.df_actual = cargar_datos(archivo_actual)

df = st.session_state.df_actual

# ==========================================================
# DASHBOARD
# ==========================================================

st.markdown("## 📊 Dashboard")

total = len(df)
pendientes = len(df[df["Estado"] == "Pendiente"])
agendados = len(df[df["Estado"] == "Agendado"])
renovados = len(df[df["Estado"] == "Renovado"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", total)
col2.metric("Pendientes", pendientes)
col3.metric("Agendados", agendados)
col4.metric("Renovados", renovados)

# ==========================================================
# FILTROS DEBAJO DEL DASHBOARD
# ==========================================================

st.markdown("## 🔎 Filtros")

colf1, colf2, colf3 = st.columns(3)

fecha_min = df["Fecha_Renovacion"].min()
fecha_max = df["Fecha_Renovacion"].max()

with colf1:
    fecha_inicio = st.date_input("Desde", fecha_min if pd.notna(fecha_min) else datetime.today())

with colf2:
    fecha_fin = st.date_input("Hasta", fecha_max if pd.notna(fecha_max) else datetime.today())

with colf3:
    sedes = ["Todas"] + sorted(df["Sede"].dropna().unique().tolist())
    sede_sel = st.selectbox("Sede", sedes)

df_filtrado = df.copy()

if pd.notna(fecha_min):
    df_filtrado = df_filtrado[
        (df_filtrado["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
        (df_filtrado["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
    ]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

# ==========================================================
# LISTADO
# ==========================================================

st.markdown("## 📋 Clientes")

for i, row in df_filtrado.iterrows():

    with st.container():
        colA, colB, colC, colD = st.columns([2,2,2,2])

        colA.write(f"**Cliente:** {row['Cliente']}")
        colB.write(f"📞 {row['Telefono']}")
        colC.write(f"🚗 {row['Placa']}")

        estado_actual = row["Estado"]

        nuevo_estado = colD.selectbox(
            "Estado",
            ["Pendiente", "Agendado", "Renovado"],
            index=["Pendiente", "Agendado", "Renovado"].index(estado_actual),
            key=f"estado_{i}"
        )

        if nuevo_estado != estado_actual:
            st.session_state.df_actual.at[i, "Estado"] = nuevo_estado
            guardar_datos(st.session_state.df_actual, archivo_actual)
            st.rerun()



