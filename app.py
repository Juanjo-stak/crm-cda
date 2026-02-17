import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil

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

if rol_actual == "admin":
    tab_crm, tab_admin = st.tabs(["📊 CRM", "👑 Panel Administración"])
else:
    tab_crm = st.tabs(["📊 CRM"])[0]

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

    # ==================================================
    # ELIMINAR BASE
    # ==================================================
    st.sidebar.divider()
    st.sidebar.subheader("🗑 Eliminar Base de Datos")

    if st.sidebar.button("Eliminar base seleccionada"):
        try:
            os.remove(ARCHIVO)
            st.sidebar.success("Base eliminada correctamente")
            st.rerun()
        except Exception:
            st.sidebar.error("Error al eliminar la base")

    # ==================================================
    # CARGAR DATA
    # ==================================================

    df = pd.read_excel(ARCHIVO)
    df.columns = df.columns.str.strip()

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    def link_whatsapp(nombre, placa, telefono, fecha):
        if pd.isna(telefono):
            return None

        telefono = str(telefono).replace(".0","").replace(" ","").replace("-","")

        if not telefono.startswith("57"):
            telefono = "57" + telefono

        fecha_texto = fecha.strftime("%d/%m/%Y")

        mensaje = f"""Hola {nombre}, soy Juan José 👋

Tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión? 🚗✅"""

        mensaje = urllib.parse.quote(mensaje)

        return f"https://wa.me/{telefono}?text={mensaje}"

    estados = ["Pendiente","Agendado","Renovado"]

    for i,row in df.iterrows():

        col1,col2,col3,col4 = st.columns(4)

        col1.write(f"**{row.get('Placa','')}**")
        col1.write(row.get("Cliente",""))

        col2.write(row["Fecha_Renovacion"])

        estado_actual = row["Estado"]

        estado = col3.selectbox(
            "Estado",
            estados,
            index=estados.index(estado_actual),
            key=f"estado_{i}"
        )

        if estado != estado_actual:
            df.loc[i,"Estado"] = estado
            df.to_excel(ARCHIVO, index=False)
            st.rerun()

        if "Telefono" in df.columns:

            # Botón WhatsApp verde
            url = link_whatsapp(
                row.get("Cliente",""),
                row.get("Placa",""),
                row.get("Telefono",""),
                row["Fecha_Renovacion"]
            )

            if url:
                col4.markdown(
                    f"""
                    <a href="{url}" target="_blank">
                        <button style="
                            width:100%;
                            padding:10px;
                            border-radius:8px;
                            background-color:#25D366;
                            color:white;
                            font-weight:bold;
                            border:none;
                            cursor:pointer;
                            margin-bottom:5px;">
                            📲 WhatsApp
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

            # Botón Llamar azul
            telefono = str(row.get("Telefono","")).replace(".0","").replace(" ","").replace("-","")

            if telefono:

                if not telefono.startswith("57"):
                    telefono = "57" + telefono

                link_llamada = f"tel:+{telefono}"

                col4.markdown(
                    f"""
                    <a href="{link_llamada}">
                        <button style="
                            width:100%;
                            padding:10px;
                            border-radius:8px;
                            background-color:#1f77b4;
                            color:white;
                            font-weight:bold;
                            border:none;
                            cursor:pointer;">
                            📞 Llamar
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

        st.divider()

