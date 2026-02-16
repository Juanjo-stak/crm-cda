import streamlit as st
import pandas as pd
import json
import os
import webbrowser
from datetime import datetime
import locale

# ===============================
# CONFIGURACION
# ===============================
st.set_page_config(page_title="CRM CDA", layout="wide")

CARPETA_BD = "bases_datos"
ARCHIVO_USUARIOS = "usuarios.json"

os.makedirs(CARPETA_BD, exist_ok=True)

# ===============================
# FECHA EN ESPAÑOL
# ===============================
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except:
    pass

def fecha_espanol():
    hoy = datetime.now()
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    meses = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]

    return f"{dias[hoy.weekday()]} {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

# ===============================
# USUARIOS
# ===============================
def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        usuarios = {
            "juanjo": {"password": "cda2026", "rol": "admin"}
        }
        with open(ARCHIVO_USUARIOS,"w") as f:
            json.dump(usuarios,f,indent=4)
    with open(ARCHIVO_USUARIOS,"r") as f:
        return json.load(f)

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS,"w") as f:
        json.dump(data,f,indent=4)

# ===============================
# LOGIN
# ===============================
if "login" not in st.session_state:
    st.session_state.login=False
    st.session_state.usuario=None
    st.session_state.rol=None

def login():
    st.title("🔐 CRM CDA - Acceso")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        usuarios = cargar_usuarios()

        if usuario in usuarios and usuarios[usuario]["password"] == password:
            st.session_state.login=True
            st.session_state.usuario=usuario
            st.session_state.rol=usuarios[usuario]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.login:
    login()
    st.stop()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("🚗 CRM CDA")
st.sidebar.write(f"👤 {st.session_state.usuario}")
st.sidebar.write(f"📅 {fecha_espanol()}")

# ===============================
# SUBIR BASES DE DATOS
# ===============================
st.sidebar.subheader("📂 Bases de datos")

archivo = st.sidebar.file_uploader("Subir Excel", type=["xlsx"])

if archivo:
    ruta = os.path.join(CARPETA_BD, archivo.name)
    with open(ruta,"wb") as f:
        f.write(archivo.getbuffer())
    st.sidebar.success("Base subida ✅")

bases = os.listdir(CARPETA_BD)

if len(bases)==0:
    st.warning("Sube una base primero")
    st.stop()

base_seleccionada = st.sidebar.selectbox("Elegir base", bases)

ruta_base = os.path.join(CARPETA_BD, base_seleccionada)
df = pd.read_excel(ruta_base)

# ===============================
# ASESORES
# ===============================
if "Asesor" not in df.columns:
    df["Asesor"]="Sin asignar"

# ===============================
# FILTRO POR USUARIO
# ===============================
df_filtrado = df.copy()

if st.session_state.rol == "asesor":
    df_filtrado = df_filtrado[
        df_filtrado["Asesor"] == st.session_state.usuario
    ]

# ===============================
# PANEL ADMIN
# ===============================
if st.session_state.rol=="admin":

    st.sidebar.divider()
    st.sidebar.subheader("👑 Panel Admin")

    usuarios = cargar_usuarios()

    nuevo_user = st.sidebar.text_input("Nuevo usuario")
    nueva_pass = st.sidebar.text_input("Clave", type="password")
    rol = st.sidebar.selectbox("Rol",["asesor","viewer","admin"])

    if st.sidebar.button("Crear usuario"):
        usuarios[nuevo_user] = {
            "password": nueva_pass,
            "rol": rol
        }
        guardar_usuarios(usuarios)
        st.sidebar.success("Usuario creado")

# ===============================
# FUNCION WHATSAPP BUSINESS
# ===============================
def abrir_whatsapp(numero, mensaje):

    numero = str(numero).replace(" ","").replace("+","")

    if not numero.startswith("57"):
        numero = "57"+numero

    texto = mensaje.replace(" ","%20")

    # prioridad whatsapp business
    url = f"whatsapp://send?phone={numero}&text={texto}"

    try:
        webbrowser.open(url)
    except:
        webbrowser.open(f"https://wa.me/{numero}?text={texto}")

# ===============================
# INTERFAZ PRINCIPAL
# ===============================
st.title("📋 Clientes CDA")

busqueda = st.text_input("Buscar cliente")

if busqueda:
    df_filtrado = df_filtrado[
        df_filtrado.astype(str).apply(
            lambda row: row.str.contains(busqueda, case=False).any(),
            axis=1
        )
    ]

usuarios = list(cargar_usuarios().keys())

for i, fila in df_filtrado.iterrows():

    col1,col2,col3,col4 = st.columns([3,2,2,2])

    col1.write(fila.iloc[0])

    telefono = fila.get("Telefono","")

    mensaje = f"Hola, te contactamos del CDA para tu renovación técnico mecánica."

    if col2.button("📲 WhatsApp", key=f"wa{i}"):
        abrir_whatsapp(telefono, mensaje)

    # ADMIN asigna asesor
    if st.session_state.rol=="admin":
        asesor = col3.selectbox(
            "Asignar",
            usuarios,
            index=usuarios.index(fila["Asesor"]) if fila["Asesor"] in usuarios else 0,
            key=f"asesor{i}"
        )

        df.loc[i,"Asesor"]=asesor

# ===============================
# GUARDAR CAMBIOS
# ===============================
if st.button("💾 Guardar cambios"):
    df.to_excel(ruta_base, index=False)
    st.success("Base actualizada ✅")
