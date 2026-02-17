import streamlit as st
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="CRM CDA Occidente", layout="wide")

CARPETA_USUARIOS = "crm_usuarios"
ARCHIVO_USUARIOS = "usuarios.json"

os.makedirs(CARPETA_USUARIOS, exist_ok=True)

# =========================
# CREAR ADMIN SI NO EXISTE
# =========================

if not os.path.exists(ARCHIVO_USUARIOS):
    usuarios_inicial = {
        "admin": {
            "password": "admin123",
            "rol": "admin"
        }
    }
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(usuarios_inicial, f)

with open(ARCHIVO_USUARIOS, "r") as f:
    usuarios = json.load(f)

# =========================
# LOGIN
# =========================

if "usuario" not in st.session_state:
    st.title("🔐 Login CRM")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == pwd:
            st.session_state.usuario = user
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

usuario_actual = st.session_state.usuario
rol_actual = st.session_state.rol

# =========================
# CREAR CARPETA DEL USUARIO
# =========================

carpeta_usuario = os.path.join(CARPETA_USUARIOS, usuario_actual)
carpeta_bases = os.path.join(carpeta_usuario, "bases")

os.makedirs(carpeta_bases, exist_ok=True)

# =========================
# FUNCION WHATSAPP
# =========================

def link_whatsapp(nombre, placa, telefono, sede, fecha):

    telefono = str(telefono).replace(".0","").replace(" ","")
    if not telefono.startswith("57"):
        telefono = "57" + telefono

    fecha_texto = fecha.strftime("%d/%m/%Y")

    mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente {sede}.

Tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión hoy? 🚗✅"""

    mensaje = urllib.parse.quote(mensaje)

    return f"https://wa.me/{telefono}?text={mensaje}"

# =========================
# TABS
# =========================

if rol_actual == "admin":
    tab1, tab2 = st.tabs(["📊 CRM", "👥 Administración"])
else:
    tab1 = st.tabs(["📊 CRM"])[0]

# =========================
# CRM TAB
# =========================

with tab1:

    st.title(f"Bienvenido {usuario_actual}")

    st.sidebar.header("📂 Bases")

    archivo = st.sidebar.file_uploader("Subir base", type=["xlsx"])

    if archivo:
        ruta = os.path.join(carpeta_bases, archivo.name)
        with open(ruta, "wb") as f:
            f.write(archivo.getbuffer())
        st.success("Base guardada")
        st.rerun()

    # ADMIN puede ver TODAS las bases
    if rol_actual == "admin":
        todas_bases = []
        for carpeta in os.listdir(CARPETA_USUARIOS):
            ruta_bases = os.path.join(CARPETA_USUARIOS, carpeta, "bases")
            if os.path.exists(ruta_bases):
                for archivo in os.listdir(ruta_bases):
                    if archivo.endswith(".xlsx"):
                        todas_bases.append(
                            (archivo, os.path.join(ruta_bases, archivo))
                        )

        nombres = [b[0] for b in todas_bases]
        seleccion = st.sidebar.selectbox("Seleccionar base", nombres)

        ruta_base = dict(todas_bases)[seleccion]

    else:
        bases = [f for f in os.listdir(carpeta_bases) if f.endswith(".xlsx")]

        if not bases:
            st.warning("No tienes bases cargadas")
            st.stop()

        seleccion = st.sidebar.selectbox("Seleccionar base", bases)
        ruta_base = os.path.join(carpeta_bases, seleccion)

    # =========================
    # CARGAR DATOS
    # =========================

    df = pd.read_excel(ruta_base)
    df.columns = df.columns.str.strip()

    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce"
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    # =========================
    # DASHBOARD
    # =========================

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df["Estado"]=="Renovado").sum())

    st.divider()

    # =========================
    # LISTADO
    # =========================

    for i,row in df.iterrows():

        col1,col2,col3,col4 = st.columns(4)

        col1.write(f"**{row['Placa']}**")
        col1.write(row["Cliente"])

        col2.write(row["Fecha_Renovacion"].date())
        col2.write(row["Sede"])

        estado = col3.selectbox(
            "Estado",
            ["Pendiente","Agendado","Renovado"],
            index=["Pendiente","Agendado","Renovado"].index(row["Estado"]),
            key=f"{i}"
        )

        df.loc[i,"Estado"] = estado

        url = link_whatsapp(
            row["Cliente"],
            row["Placa"],
            row["Telefono"],
            row["Sede"],
            row["Fecha_Renovacion"]
        )

        col4.link_button("📲 WhatsApp", url)

        st.divider()

    if st.button("💾 Guardar"):
        df.to_excel(ruta_base, index=False)
        st.success("Cambios guardados")

# =========================
# ADMIN TAB
# =========================

if rol_actual == "admin":

    with tab2:

        st.title("Panel de Administración")

        nuevo_user = st.text_input("Nuevo usuario")
        nueva_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear usuario"):

            if nuevo_user in usuarios:
                st.error("Ya existe")
            else:
                usuarios[nuevo_user] = {
                    "password": nueva_pass,
                    "rol": "usuario"
                }

                with open(ARCHIVO_USUARIOS, "w") as f:
                    json.dump(usuarios, f)

                os.makedirs(
                    os.path.join(CARPETA_USUARIOS, nuevo_user, "bases"),
                    exist_ok=True
                )

                st.success("Usuario creado")
