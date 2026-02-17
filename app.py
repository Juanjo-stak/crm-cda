import streamlit as st
import pandas as pd
import urllib.parse
import os
import json

# =========================
# CONFIGURACIÓN
# =========================

st.set_page_config(page_title="CRM CDA", layout="wide")

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_BASES = "bases"

os.makedirs(CARPETA_BASES, exist_ok=True)

# =========================
# USUARIOS
# =========================

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS) or os.path.getsize(ARCHIVO_USUARIOS) == 0:
        with open(ARCHIVO_USUARIOS, "w") as f:
            json.dump(
                {"admin": {"password": "admin123", "rol": "admin"}},
                f,
                indent=4
            )
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

def pantalla_login():
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
    pantalla_login()
    st.stop()

# =========================
# CREAR CARPETA DEL USUARIO
# =========================

usuario_actual = st.session_state.usuario
rol_actual = st.session_state.rol

carpeta_usuario = os.path.join(CARPETA_BASES, usuario_actual)
os.makedirs(carpeta_usuario, exist_ok=True)

# =========================
# HEADER
# =========================

st.title("🚗 CRM Renovaciones CDA")
st.write(f"👤 Usuario: {usuario_actual} | Rol: {rol_actual}")

# =========================
# PESTAÑAS
# =========================

if rol_actual == "admin":
    tab1, tab2 = st.tabs(["📊 CRM", "👑 Panel Administración"])
else:
    tab1 = st.tabs(["📊 CRM"])[0]

# ==========================================================
# ======================= TAB CRM ==========================
# ==========================================================

with tab1:

    st.sidebar.header("📂 Bases de datos")

    # -------------------------
    # SUBIR BASE
    # -------------------------

    archivo_subido = st.sidebar.file_uploader("Subir nueva base", type=["xlsx"])

    if archivo_subido:
        ruta_guardado = os.path.join(carpeta_usuario, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("✅ Base guardada")
        st.rerun()

    # -------------------------
    # LISTAR BASES SEGÚN ROL
    # -------------------------

    if rol_actual == "admin":

        bases_disponibles = []

        for usuario in os.listdir(CARPETA_BASES):
            ruta_user = os.path.join(CARPETA_BASES, usuario)
            for archivo in os.listdir(ruta_user):
                if archivo.endswith(".xlsx"):
                    bases_disponibles.append(
                        (f"{usuario} - {archivo}", os.path.join(ruta_user, archivo))
                    )

        if not bases_disponibles:
            st.warning("⚠️ No hay bases cargadas")
            st.stop()

        nombres = [x[0] for x in bases_disponibles]
        seleccion = st.sidebar.selectbox("Seleccionar base", nombres)
        ARCHIVO = dict(bases_disponibles)[seleccion]

    else:

        bases_disponibles = [
            f for f in os.listdir(carpeta_usuario)
            if f.endswith(".xlsx")
        ]

        if not bases_disponibles:
            st.warning("⚠️ No tienes bases cargadas")
            st.stop()

        seleccion = st.sidebar.selectbox("Seleccionar base", bases_disponibles)
        ARCHIVO = os.path.join(carpeta_usuario, seleccion)

    # =========================
    # CARGAR DATOS
    # =========================

    df = pd.read_excel(ARCHIVO)
    df.columns = df.columns.str.strip()

    # Detectar columna fecha automáticamente
    columnas_lower = {col.lower(): col for col in df.columns}

    posibles_fechas = [
        "fecha_renovacion",
        "fecha",
        "vencimiento",
        "fecha vencimiento",
        "fecca"
    ]

    columna_fecha_real = None

    for posible in posibles_fechas:
        if posible in columnas_lower:
            columna_fecha_real = columnas_lower[posible]
            break

    if columna_fecha_real is None:
        st.error("❌ No se encontró columna de fecha.")
        st.write("Columnas detectadas:", list(df.columns))
        st.stop()

    df.rename(columns={columna_fecha_real: "Fecha_Renovacion"}, inplace=True)

    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    # =========================
    # DASHBOARD
    # =========================

    st.markdown("## 📊 Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df["Estado"]=="Renovado").sum())

    st.divider()

    # =========================
    # WHATSAPP
    # =========================

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

    # =========================
    # LISTADO
    # =========================

    estados = ["Pendiente","Agendado","Renovado"]

    for i,row in df.iterrows():

        col1,col2,col3,col4 = st.columns(4)

        col1.write(f"**{row.get('Placa','')}**")
        col1.write(row.get("Cliente",""))

        col2.write(row["Fecha_Renovacion"].date())

        estado = col3.selectbox(
            "Estado",
            estados,
            index=estados.index(row["Estado"]),
            key=f"{i}"
        )

        df.loc[i,"Estado"] = estado

        if "Telefono" in df.columns:
            url = link_whatsapp(
                row.get("Cliente",""),
                row.get("Placa",""),
                row.get("Telefono",""),
                row["Fecha_Renovacion"]
            )

            if url:
                col4.link_button("📲 WhatsApp", url)

        st.divider()

    if st.button("💾 Guardar cambios"):
        df.to_excel(ARCHIVO, index=False)
        st.success("Cambios guardados ✅")

# ==========================================================
# =================== PANEL ADMIN ==========================
# ==========================================================

if rol_actual == "admin":

    with tab2:

        st.header("👑 Panel de Administración")

        usuarios = cargar_usuarios()

        nuevo_user = st.text_input("Usuario nuevo")
        nueva_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear Usuario"):
            if nuevo_user in usuarios:
                st.error("El usuario ya existe")
            else:
                usuarios[nuevo_user] = {
                    "password": nueva_pass,
                    "rol": "asesor"
                }
                guardar_usuarios(usuarios)
                os.makedirs(os.path.join(CARPETA_BASES, nuevo_user), exist_ok=True)
                st.success("Usuario creado correctamente ✅")
                st.rerun()

        st.divider()

        st.subheader("Usuarios registrados")

        for user in usuarios.keys():
            st.write(user)



