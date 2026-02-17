import streamlit as st
import pandas as pd
import os
import json
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="CRM CDA Occidente", layout="wide")

# =========================
# CONFIGURACIÓN
# =========================

CARPETA_RAIZ = "crm_data"
CARPETA_USUARIOS = os.path.join(CARPETA_RAIZ, "usuarios")
ARCHIVO_USUARIOS = os.path.join(CARPETA_RAIZ, "usuarios.json")

os.makedirs(CARPETA_USUARIOS, exist_ok=True)

# =========================
# CREAR ARCHIVO USUARIOS SI NO EXISTE
# =========================

if not os.path.exists(ARCHIVO_USUARIOS):
    usuarios_inicial = {
        "admin": {
            "password": "admin123",
            "rol": "admin"
        }
    }
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(usuarios_inicial, f, indent=4)

# Cargar usuarios seguro
try:
    with open(ARCHIVO_USUARIOS, "r") as f:
        usuarios = json.load(f)
except:
    st.error("El archivo usuarios.json está corrupto. Elimínalo y reinicia.")
    st.stop()

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
# CREAR CARPETA USUARIO
# =========================

carpeta_usuario = os.path.join(CARPETA_USUARIOS, usuario_actual)
carpeta_bases_usuario = os.path.join(carpeta_usuario, "bases")

os.makedirs(carpeta_bases_usuario, exist_ok=True)

# =========================
# FUNCIÓN WHATSAPP
# =========================

def link_whatsapp(nombre, placa, telefono, sede, fecha):

    telefono = str(telefono).replace(".0", "").replace(" ", "")

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
    tab_crm, tab_admin = st.tabs(["📊 CRM", "👥 Administración"])
else:
    tab_crm = st.tabs(["📊 CRM"])[0]

# =========================
# CRM
# =========================

with tab_crm:

    st.title(f"📊 CRM - {usuario_actual}")

    st.sidebar.header("📂 Bases de datos")

    archivo_subido = st.sidebar.file_uploader("Subir base", type=["xlsx"])

    if archivo_subido:
        ruta_guardado = os.path.join(carpeta_bases_usuario, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.success("Base guardada correctamente")
        st.rerun()

    # =========================
    # SELECCIÓN BASES
    # =========================

    if rol_actual == "admin":

        lista_bases = []

        for user_folder in os.listdir(CARPETA_USUARIOS):
            ruta_bases = os.path.join(CARPETA_USUARIOS, user_folder, "bases")
            if os.path.exists(ruta_bases):
                for archivo in os.listdir(ruta_bases):
                    if archivo.endswith(".xlsx"):
                        nombre_visible = f"{user_folder} - {archivo}"
                        lista_bases.append((nombre_visible, os.path.join(ruta_bases, archivo)))

        if not lista_bases:
            st.warning("No hay bases disponibles")
            st.stop()

        nombres = [x[0] for x in lista_bases]
        seleccion = st.sidebar.selectbox("Seleccionar base", nombres)

        ruta_base = dict(lista_bases)[seleccion]

    else:

        bases_usuario = [f for f in os.listdir(carpeta_bases_usuario) if f.endswith(".xlsx")]

        if not bases_usuario:
            st.warning("No tienes bases cargadas")
            st.stop()

        seleccion = st.sidebar.selectbox("Seleccionar base", bases_usuario)
        ruta_base = os.path.join(carpeta_bases_usuario, seleccion)

    # =========================
    # CARGAR BASE SEGURO
    # =========================

    try:
        df = pd.read_excel(ruta_base)
    except:
        st.error("Error leyendo la base. Puede estar dañada.")
        st.stop()

    df.columns = df.columns.str.strip()

    if "Fecha_Renovacion" not in df.columns:
        st.error("La base debe tener columna 'Fecha'")
        st.stop()

    df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    # =========================
    # DASHBOARD
    # =========================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df["Estado"]=="Renovado").sum())

    st.divider()

    # =========================
    # LISTADO
    # =========================

    for i, row in df.iterrows():

        col1, col2, col3, col4 = st.columns(4)

        col1.write(f"**{row.get('Placa','')}**")
        col1.write(row.get("Cliente",""))

        col2.write(row["Fecha_Renovacion"].date())
        col2.write(row.get("Sede",""))

        estado = col3.selectbox(
            "Estado",
            ["Pendiente","Agendado","Renovado"],
            index=["Pendiente","Agendado","Renovado"].index(row["Estado"]),
            key=f"{i}"
        )

        df.loc[i,"Estado"] = estado

        if "Telefono" in df.columns:
            url = link_whatsapp(
                row.get("Cliente",""),
                row.get("Placa",""),
                row.get("Telefono",""),
                row.get("Sede",""),
                row["Fecha_Renovacion"]
            )
            col4.link_button("📲 WhatsApp", url)

        st.divider()

    if st.button("💾 Guardar cambios"):
        df.to_excel(ruta_base, index=False)
        st.success("Cambios guardados correctamente")

# =========================
# ADMIN
# =========================

if rol_actual == "admin":

    with tab_admin:

        st.title("👥 Panel Administración")

        nuevo_usuario = st.text_input("Nuevo usuario")
        nueva_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear usuario"):

            if nuevo_usuario in usuarios:
                st.error("El usuario ya existe")
            else:
                usuarios[nuevo_usuario] = {
                    "password": nueva_pass,
                    "rol": "usuario"
                }

                with open(ARCHIVO_USUARIOS, "w") as f:
                    json.dump(usuarios, f, indent=4)

                os.makedirs(
                    os.path.join(CARPETA_USUARIOS, nuevo_usuario, "bases"),
                    exist_ok=True
                )

                st.success("Usuario creado correctamente")
                st.rerun()

                st.success("Usuario creado")
