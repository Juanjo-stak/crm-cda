import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# ======================================================
# CONFIGURACIÓN INICIAL
# ======================================================

st.set_page_config(page_title="CRM Renovaciones CDA", layout="wide")

CARPETA_USUARIOS = "usuarios"
CARPETA_BASES = "bases_datos"

os.makedirs(CARPETA_USUARIOS, exist_ok=True)
os.makedirs(CARPETA_BASES, exist_ok=True)

# ======================================================
# FUNCIONES USUARIOS
# ======================================================

def cargar_usuarios():
    archivo = os.path.join(CARPETA_USUARIOS, "usuarios.json")
    if not os.path.exists(archivo):
        usuarios_base = {
            "admin": {"password": "admin123", "rol": "admin"}
        }
        with open(archivo, "w") as f:
            json.dump(usuarios_base, f)
        return usuarios_base
    with open(archivo, "r") as f:
        return json.load(f)

def guardar_usuarios(data):
    archivo = os.path.join(CARPETA_USUARIOS, "usuarios.json")
    with open(archivo, "w") as f:
        json.dump(data, f)

usuarios = cargar_usuarios()

# ======================================================
# LOGIN
# ======================================================

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Iniciar sesión")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == pwd:
            st.session_state.login = True
            st.session_state.usuario = user
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

usuario_actual = st.session_state.usuario
rol_actual = st.session_state.rol

# ======================================================
# TÍTULO
# ======================================================

st.title("🚗 CRM Renovaciones CDA")
st.write(f"👤 Usuario: {usuario_actual} | Rol: {rol_actual}")

# ======================================================
# 🔴 CERRAR SESIÓN (AGREGADO)
# ======================================================

col_logout1, col_logout2 = st.columns([6,1])

with col_logout2:
    if st.button("🚪 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

# ======================================================
# PANEL ADMIN
# ======================================================

if rol_actual == "admin":
    st.sidebar.header("⚙ Panel Administración")

    nuevo_user = st.sidebar.text_input("Nuevo usuario")
    nueva_pass = st.sidebar.text_input("Contraseña", type="password")
    nuevo_rol = st.sidebar.selectbox("Rol", ["usuario", "admin"])

    if st.sidebar.button("Crear usuario"):
        if nuevo_user not in usuarios:
            usuarios[nuevo_user] = {"password": nueva_pass, "rol": nuevo_rol}
            guardar_usuarios(usuarios)
            os.makedirs(os.path.join(CARPETA_BASES, nuevo_user), exist_ok=True)
            st.sidebar.success("Usuario creado")
        else:
            st.sidebar.error("Ya existe")

    eliminar_user = st.sidebar.selectbox("Eliminar usuario", list(usuarios.keys()))
    if st.sidebar.button("Eliminar usuario"):
        if eliminar_user != "admin":
            usuarios.pop(eliminar_user)
            guardar_usuarios(usuarios)
            st.sidebar.success("Usuario eliminado")
        else:
            st.sidebar.error("No puedes eliminar admin")

# ======================================================
# CARGA DE BASES
# ======================================================

st.sidebar.header("📂 Subir Base de Datos")

archivo_subido = st.sidebar.file_uploader("Sube tu archivo CSV", type=["csv"])

ruta_user = os.path.join(CARPETA_BASES, usuario_actual)
os.makedirs(ruta_user, exist_ok=True)

if archivo_subido:
    ruta_archivo = os.path.join(ruta_user, archivo_subido.name)
    with open(ruta_archivo, "wb") as f:
        f.write(archivo_subido.getbuffer())
    st.sidebar.success("Base subida correctamente")

# ======================================================
# LISTAR BASES
# ======================================================

bases_disponibles = []

if rol_actual == "admin":
    for usuario in os.listdir(CARPETA_BASES):
        ruta = os.path.join(CARPETA_BASES, usuario)
        if os.path.isdir(ruta):
            for archivo in os.listdir(ruta):
                bases_disponibles.append(os.path.join(ruta, archivo))
else:
    for archivo in os.listdir(ruta_user):
        bases_disponibles.append(os.path.join(ruta_user, archivo))

if not bases_disponibles:
    st.warning("No hay bases disponibles")
    st.stop()

archivo_seleccionado = st.selectbox("Selecciona Base", bases_disponibles)

df = pd.read_csv(archivo_seleccionado)

# ======================================================
# FILTROS
# ======================================================

st.subheader("📊 Dashboard")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    fecha_inicio = st.date_input("Desde", pd.to_datetime(df["Fecha_Renovacion"]).min())

with col_f2:
    fecha_fin = st.date_input("Hasta", pd.to_datetime(df["Fecha_Renovacion"]).max())

with col_f3:
    sedes = ["Todas"] + sorted(df["Sede"].dropna().unique().tolist())
    sede_sel = st.selectbox("Sede", sedes)

df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha_Renovacion"])

df_filtrado = df[
    (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
    (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

# ======================================================
# DASHBOARD INTERACTIVO
# ======================================================

total = len(df_filtrado)
agendados = len(df_filtrado[df_filtrado["Estado"] == "Agendado"])
renovados = len(df_filtrado[df_filtrado["Estado"] == "Renovado"])

col1, col2, col3 = st.columns(3)

col1.metric("Total", total)
col2.metric("Agendados", agendados)
col3.metric("Renovados", renovados)

# ======================================================
# TABLA CON BOTONES
# ======================================================

st.subheader("📋 Registros")

for index, fila in df_filtrado.iterrows():
    col1, col2, col3, col4 = st.columns([2,2,2,2])

    col1.write(fila["Nombre"])
    col2.write(fila["Telefono"])

    link_whatsapp = f"https://wa.me/{fila['Telefono']}"

    with col3:
        st.link_button("💬 WhatsApp", link_whatsapp)

    # 🔴 BOTÓN LLAMAR (AGREGADO)
    with col4:
        telefono_limpio = str(fila["Telefono"]).replace(" ", "").replace("-", "")
        link_llamada = f"tel:{telefono_limpio}"
        st.link_button("📞 Llamar", link_llamada)

    estado = st.selectbox(
        "Estado",
        ["Pendiente", "Agendado", "Renovado"],
        index=["Pendiente", "Agendado", "Renovado"].index(fila["Estado"]),
        key=index
    )

    df.loc[index, "Estado"] = estado

st.success("Sistema funcionando correctamente ✅")



