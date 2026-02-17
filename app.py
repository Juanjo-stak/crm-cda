import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
from datetime import datetime

# =========================
# CONFIGURACIÓN
# =========================

st.set_page_config(page_title="CRM CDA", layout="wide")

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_BASES = "bases"
os.makedirs(CARPETA_BASES, exist_ok=True)

# =========================
# FUNCIONES USUARIOS
# =========================

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, "w") as f:
            json.dump({"admin": {"password": "admin123", "rol": "admin"}}, f)
    with open(ARCHIVO_USUARIOS, "r") as f:
        return json.load(f)

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# SESSION STATE
# =========================

if "login" not in st.session_state:
    st.session_state.login = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "rol" not in st.session_state:
    st.session_state.rol = None

# =========================
# LOGIN
# =========================

def login():
    st.title("🔐 CRM CDA - Acceso")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        usuarios = cargar_usuarios()

        if usuario in usuarios and usuarios[usuario]["password"] == password:
            st.session_state.login = True
            st.session_state.usuario = usuario
            st.session_state.rol = usuarios[usuario]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.login:
    login()
    st.stop()

# =========================
# TÍTULO PRINCIPAL
# =========================

st.title("🚗 CRM Renovaciones CDA")
st.write(f"👤 Usuario: {st.session_state.usuario} | Rol: {st.session_state.rol}")

# =========================
# CREAR PESTAÑAS
# =========================

if st.session_state.rol == "admin":
    tab1, tab2 = st.tabs(["📊 CRM", "👑 Panel Administración"])
else:
    tab1 = st.tabs(["📊 CRM"])[0]

# ==========================================================
# ======================= TAB CRM ==========================
# ==========================================================

with tab1:

    # -------------------------
    # SUBIR BASE
    # -------------------------

    st.sidebar.header("📂 Bases de datos")

    archivo_subido = st.sidebar.file_uploader(
        "Subir nueva base",
        type=["xlsx"]
    )

    if archivo_subido:
        ruta_guardado = os.path.join(CARPETA_BASES, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("✅ Base guardada")
        st.rerun()

    bases_disponibles = [
        f for f in os.listdir(CARPETA_BASES)
        if f.endswith(".xlsx")
    ]

    if not bases_disponibles:
        st.warning("⚠️ No hay bases cargadas aún")
        st.stop()

    base_seleccionada = st.sidebar.selectbox(
        "Seleccionar base",
        bases_disponibles
    )

    ARCHIVO = os.path.join(CARPETA_BASES, base_seleccionada)

    # -------------------------
    # CARGAR DATOS
    # -------------------------

    @st.cache_data
    def cargar_datos(archivo):
        df = pd.read_excel(archivo)
        df.columns = df.columns.str.strip()

        columnas = {
            "Placa ": "Placa",
            "Cliente": "Cliente",
            "Telefono": "Telefono",
            "Fecha": "Fecha_Renovacion",
            "fecca": "Fecha_Renovacion",
            "sede": "Sede"
        }

        df.rename(columns=columnas, inplace=True)

        df["Fecha_Renovacion"] = pd.to_datetime(
            df["Fecha_Renovacion"],
            errors="coerce",
            dayfirst=True
        )

        df = df[df["Fecha_Renovacion"].notna()]

        if "Estado" not in df.columns:
            df["Estado"] = "Pendiente"

        return df

    df = cargar_datos(ARCHIVO)

    # -------------------------
    # DASHBOARD
    # -------------------------

    st.markdown("## 📊 Dashboard")

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Contactados", (df["Estado"]=="Contactado").sum())
    c4.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c5.metric("Renovados", (df["Estado"]=="Renovado").sum())

    # -------------------------
    # FUNCIÓN WHATSAPP
    # -------------------------

    def link_whatsapp(nombre, placa, telefono, sede, fecha):

        if pd.isna(telefono):
            return None

        telefono = str(telefono).replace(".0", "").replace(" ", "").replace("-", "")

        if not telefono.startswith("57"):
            telefono = "57" + telefono

        dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
        meses = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]

        fecha_texto = f"{dias[fecha.weekday()]} {fecha.day} de {meses[fecha.month-1]} de {fecha.year}"

        mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente {sede}.

Tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión hoy? 🚗✅"""

        mensaje = urllib.parse.quote(mensaje)

        return f"https://wa.me/{telefono}?text={mensaje}"

    # -------------------------
    # LISTADO
    # -------------------------

    estados = ["Pendiente","Contactado","Agendado","Renovado"]

    for i,row in df.iterrows():

        col1,col2,col3,col4 = st.columns([2,2,2,2])

        col1.write(f"**{row['Placa']}**")
        col1.write(row["Cliente"])

        col2.write(row["Fecha_Renovacion"].date())
        col2.write(row["Sede"])

        estado = col3.selectbox(
            "Estado",
            estados,
            index=estados.index(row["Estado"]),
            key=f"estado_{i}"
        )

        df.loc[i,"Estado"] = estado

        url = link_whatsapp(
            row["Cliente"],
            row["Placa"],
            row["Telefono"],
            row["Sede"],
            row["Fecha_Renovacion"]
        )

        if url:
            col4.link_button("📲 WhatsApp", url)
        else:
            col4.write("❌ Sin número")

        st.divider()

    if st.button("💾 Guardar cambios"):
        df.to_excel(ARCHIVO, index=False)
        st.success("Cambios guardados ✅")


# ==========================================================
# =================== TAB ADMINISTRACIÓN ===================
# ==========================================================

if st.session_state.rol == "admin":

    with tab2:

        st.header("👑 Panel de Administración")

        usuarios = cargar_usuarios()

        st.subheader("➕ Crear Usuario")

        nuevo_user = st.text_input("Usuario nuevo")
        nueva_pass = st.text_input("Contraseña", type="password")
        rol_nuevo = st.selectbox("Rol", ["asesor","viewer","admin"])

        if st.button("Crear Usuario"):
            if nuevo_user in usuarios:
                st.error("El usuario ya existe")
            else:
                usuarios[nuevo_user] = {
                    "password": nueva_pass,
                    "rol": rol_nuevo
                }
                guardar_usuarios(usuarios)
                st.success("Usuario creado correctamente ✅")
                st.rerun()

        st.divider()

        st.subheader("👥 Usuarios Registrados")

        for user, data in usuarios.items():

            col1,col2,col3 = st.columns([2,2,1])

            col1.write(user)
            col2.write(data["rol"])

            if user != "admin":
                if col3.button("Eliminar", key=f"del_{user}"):
                    del usuarios[user]
                    guardar_usuarios(usuarios)
                    st.success("Usuario eliminado")
                    st.rerun()
