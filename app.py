import streamlit as st
import pandas as pd
import os
import json
import urllib.parse

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(page_title="CRM CDA", layout="wide")

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_BASES = "bases"

os.makedirs(CARPETA_BASES, exist_ok=True)

# ======================================================
# USUARIOS
# ======================================================

def inicializar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
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

st.title("🚗 Renovaciones CDA")
st.write(f"👤 Usuario: {usuario_actual} | Rol: {rol_actual}")

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
# SIDEBAR BASES
# ======================================================

st.sidebar.header("📂 Bases de datos")

archivo_subido = st.sidebar.file_uploader("Subir Excel", type=["xlsx"])

if archivo_subido:
    ruta = os.path.join(carpeta_usuario, archivo_subido.name)
    with open(ruta, "wb") as f:
        f.write(archivo_subido.getbuffer())
    st.sidebar.success("Base subida correctamente")
    st.rerun()

bases = [
    f for f in os.listdir(carpeta_usuario)
    if f.endswith(".xlsx")
]

if not bases:
    st.warning("Sube una base Excel para comenzar")
    st.stop()

base_seleccionada = st.sidebar.selectbox("Seleccionar base", bases)

ARCHIVO = os.path.join(carpeta_usuario, base_seleccionada)

# ======================================================
# CARGAR DATA
# ======================================================

df = pd.read_excel(ARCHIVO)
df.columns = df.columns.str.strip()

# detectar fecha automáticamente
columnas_lower = {c.lower(): c for c in df.columns}

posibles = ["fecha_renovacion","fecha","vencimiento","fecha vencimiento"]

col_fecha = None
for p in posibles:
    if p in columnas_lower:
        col_fecha = columnas_lower[p]
        break

if col_fecha is None:
    st.error("No se encontró columna de fecha")
    st.stop()

df.rename(columns={col_fecha:"Fecha_Renovacion"}, inplace=True)

df["Fecha_Renovacion"] = pd.to_datetime(
    df["Fecha_Renovacion"],
    errors="coerce",
    dayfirst=True
)

df = df[df["Fecha_Renovacion"].notna()]

if "Estado" not in df.columns:
    df["Estado"] = "Pendiente"

# ======================================================
# DASHBOARD
# ======================================================

st.subheader("📊 Dashboard")

c1,c2,c3 = st.columns(3)

c1.metric("Total", len(df))
c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
c3.metric("Renovados", (df["Estado"]=="Renovado").sum())

# ======================================================
# WHATSAPP
# ======================================================

def link_whatsapp(nombre, placa, telefono, fecha):

    telefono = str(telefono).replace(".0","").replace(" ","")

    if not telefono.startswith("57"):
        telefono = "57"+telefono

    fecha_txt = fecha.strftime("%d/%m/%Y")

    mensaje = f"""Hola {nombre} 👋
Tu vehículo {placa} vence el {fecha_txt}.
¿Deseas agendar tu revisión? 🚗✅"""

    mensaje = urllib.parse.quote(mensaje)

    return f"https://wa.me/{telefono}?text={mensaje}"

# ======================================================
# LISTADO
# ======================================================

st.subheader("📋 Clientes")

estados = ["Pendiente","Agendado","Renovado"]

for i,row in df.iterrows():

    col1,col2,col3,col4 = st.columns(4)

    col1.write(f"**{row.get('Placa','')}**")
    col1.write(row.get("Cliente",""))

    col2.write(row["Fecha_Renovacion"].date())

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

        url = link_whatsapp(
            row.get("Cliente",""),
            row.get("Placa",""),
            row.get("Telefono",""),
            row["Fecha_Renovacion"]
        )

        col4.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="background:#25D366;color:white;'
            f'border:none;padding:8px;border-radius:6px;width:100%;">'
            f'💬 WhatsApp</button></a>',
            unsafe_allow_html=True
        )
