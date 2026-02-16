import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
import os

# =========================
# LOGIN
# =========================
USUARIO_CORRECTO = "juanjo"
CLAVE_CORRECTA = "cda2026"

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.title("🔐 Acceso CRM CDA")

    u = st.text_input("Usuario")
    c = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if u == USUARIO_CORRECTO and c == CLAVE_CORRECTA:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.login:
    login()
    st.stop()

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="CRM CDA", layout="wide")
st.title("🚗 CRM Renovaciones CDA")

CARPETA_BASES = "bases"
os.makedirs(CARPETA_BASES, exist_ok=True)

# =========================
# SUBIR BASE NUEVA
# =========================
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

# =========================
# LISTAR BASES DISPONIBLES
# =========================
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

# =========================
# CARGAR DATOS
# =========================
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

st.success(f"✅ Base activa: {base_seleccionada}")

# =========================
# DASHBOARD
# =========================
st.markdown("## 📊 Dashboard")

c1,c2,c3,c4,c5 = st.columns(5)

c1.metric("Total", len(df))
c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
c3.metric("Contactados", (df["Estado"]=="Contactado").sum())
c4.metric("Agendados", (df["Estado"]=="Agendado").sum())
c5.metric("Renovados", (df["Estado"]=="Renovado").sum())

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

fecha_inicio = st.sidebar.date_input(
    "Desde",
    df["Fecha_Renovacion"].min().date()
)

fecha_fin = st.sidebar.date_input(
    "Hasta",
    df["Fecha_Renovacion"].max().date()
)

sedes = ["Todas"] + sorted(df["Sede"].dropna().unique().tolist())
sede_sel = st.sidebar.selectbox("Sede", sedes)

df_filtrado = df[
    (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
    (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

# =========================
# WHATSAPP
# =========================
def link_whatsapp(nombre, placa, telefono, sede, fecha):

    telefono = str(telefono).replace(".0","").replace(" ","")
    if not telefono.startswith("57"):
        telefono = "57" + telefono

    fecha_texto = fecha.strftime("%A %d de %B de %Y")

    mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente {sede}.

Tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión hoy? 🚗✅"""

    mensaje = urllib.parse.quote(mensaje)

    return f"https://api.whatsapp.com/send?phone={telefono}&text={mensaje}"

# =========================
# LISTADO
# =========================
estados = ["Pendiente","Contactado","Agendado","Renovado"]

for i,row in df_filtrado.iterrows():

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

    col4.link_button(
        "📲 WhatsApp",
        link_whatsapp(
            row["Cliente"],
            row["Placa"],
            row["Telefono"],
            row["Sede"],
            row["Fecha_Renovacion"]
        )
    )

    st.divider()

# =========================
# GUARDAR
# =========================
if st.button("💾 Guardar cambios"):
    df.to_excel(ARCHIVO, index=False)
    st.success("Cambios guardados ✅")

