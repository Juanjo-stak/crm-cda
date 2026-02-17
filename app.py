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

st.title("🚗 CRM Renovaciones CDA")
st.write(f"👤 Usuario: {usuario_actual} | Rol: {rol_actual}")

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

    # SUBIR BASE
    archivo_subido = st.sidebar.file_uploader("Subir base Excel", type=["xlsx"])

    if archivo_subido:
        ruta_guardado = os.path.join(carpeta_usuario, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("Base guardada correctamente")
        st.rerun()

    # LISTAR BASES
    bases_disponibles = []

    if rol_actual == "admin":

        for usuario in os.listdir(CARPETA_BASES):
            ruta_user = os.path.join(CARPETA_BASES, usuario)
            if not os.path.isdir(ruta_user):
                continue
            for archivo in os.listdir(ruta_user):
                ruta_archivo = os.path.join(ruta_user, archivo)
                if os.path.isfile(ruta_archivo) and archivo.endswith(".xlsx"):
                    bases_disponibles.append(
                        (f"{usuario} - {archivo}", ruta_archivo)
                    )
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
    # CARGAR DATA
    # ==================================================

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
    # FILTROS RESTAURADOS
    # ==================================================

    st.sidebar.markdown("## 🔎 Filtros")

    filtro_estado = st.sidebar.multiselect(
        "Filtrar por estado",
        ["Pendiente","Agendado","Renovado"],
        default=["Pendiente","Agendado","Renovado"]
    )

    busqueda = st.sidebar.text_input("Buscar por placa o cliente")

    df_filtrado = df[df["Estado"].isin(filtro_estado)]

    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado.apply(
                lambda row: busqueda.lower() in str(row).lower(),
                axis=1
            )
        ]

    # ==================================================
    # DASHBOARD
    # ==================================================
# =========================
# FILTROS
# =========================

st.sidebar.header("🔎 Filtros")

# Validar que exista la columna Sede
if "Sede" not in df.columns:
    df["Sede"] = "Sin sede"

# Fechas mínima y máxima
fecha_min = df["Fecha_Renovacion"].min()
fecha_max = df["Fecha_Renovacion"].max()

# Si por alguna razón están vacías
if pd.isna(fecha_min) or pd.isna(fecha_max):
    st.warning("No hay fechas válidas en la base")
    st.stop()

fecha_inicio = st.sidebar.date_input(
    "Desde",
    fecha_min.date()
)

fecha_fin = st.sidebar.date_input(
    "Hasta",
    fecha_max.date()
)

# Selector de sede
sedes = ["Todas"] + sorted(
    df["Sede"].dropna().astype(str).unique().tolist()
)

sede_sel = st.sidebar.selectbox("Sede", sedes)

# =========================
# APLICAR FILTROS
# =========================

df_filtrado = df[
    (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
    (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

    st.markdown("## 📊 Dashboard")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", len(df_filtrado))
    c2.metric("Pendientes", (df_filtrado["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df_filtrado["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df_filtrado["Estado"]=="Renovado").sum())

    st.divider()

    # ==================================================
    # WHATSAPP
    # ==================================================

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

    # ==================================================
    # LISTADO
    # ==================================================

    estados = ["Pendiente","Agendado","Renovado"]

    for i,row in df_filtrado.iterrows():

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
        st.success("Cambios guardados correctamente")

# ======================================================
# ================= PANEL ADMIN ========================
# ======================================================

if rol_actual == "admin":

    with tab_admin:

        st.header("👑 Panel Administración")

        usuarios = cargar_usuarios()

        nuevo_user = st.text_input("Nuevo usuario")
        nueva_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear Usuario"):
            if nuevo_user in usuarios:
                st.error("El usuario ya existe")
            elif nuevo_user.strip()=="" or nueva_pass.strip()=="":
                st.error("Campos vacíos")
            else:
                usuarios[nuevo_user] = {
                    "password": nueva_pass,
                    "rol": "usuario"
                }
                guardar_usuarios(usuarios)
                os.makedirs(os.path.join(CARPETA_BASES,nuevo_user),exist_ok=True)
                st.success("Usuario creado correctamente")
                st.rerun()

        st.divider()
        st.subheader("Usuarios registrados")

        for user,datos in usuarios.items():

            col1,col2 = st.columns([3,1])

            col1.write(f"👤 {user} ({datos['rol']})")

            if user != "admin":
                if col2.button("🗑 Eliminar", key=f"del_{user}"):

                    del usuarios[user]
                    guardar_usuarios(usuarios)

                    carpeta_eliminar = os.path.join(CARPETA_BASES,user)
                    if os.path.exists(carpeta_eliminar):
                        shutil.rmtree(carpeta_eliminar)

                    st.success("Usuario eliminado")
                    st.rerun()


