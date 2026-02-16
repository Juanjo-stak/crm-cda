import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
import webbrowser

# =========================
# CONFIGURACION PAGINA
# =========================
st.set_page_config(page_title="CRM CDA", layout="wide")

st.title("🚗 CRM Renovaciones CDA")

ARCHIVO = "clientes.xlsx"

# =========================
# CARGAR BASE DE DATOS
# =========================
@st.cache_data
def cargar_datos():
    df = pd.read_excel(ARCHIVO)

    # limpiar nombres columnas
    df.columns = df.columns.str.strip()

    columnas = {
        "Placa ": "Placa",
        "Cliente": "Cliente",
        "Cedula": "Cedula",
        "Telefono": "Telefono",
        "Telefono 2": "Telefono2",
        "fecca": "Fecha_Renovacion",
        "Fecha": "Fecha_Renovacion",
        "sede": "Sede"
    }

    df.rename(columns=columnas, inplace=True)

    # convertir fecha correctamente
    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    return df


# ===== SESSION STATE (CRM EN VIVO)
df_inicial = cargar_datos()

if "df" not in st.session_state:
    st.session_state.df = df_inicial.copy()

df = st.session_state.df

st.success("✅ Base cargada correctamente")

# =========================
# DASHBOARD DINAMICO
# =========================
st.markdown("## 📊 Dashboard Comercial")

total = len(df)
pendientes = len(df[df["Estado"] == "Pendiente"])
contactados = len(df[df["Estado"] == "Contactado"])
agendados = len(df[df["Estado"] == "Agendado"])
renovados = len(df[df["Estado"] == "Renovado"])

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("📋 Total", total)
c2.metric("🟡 Pendientes", pendientes)
c3.metric("🔵 Contactados", contactados)
c4.metric("🟠 Agendados", agendados)
c5.metric("🟢 Renovados", renovados)

# =========================
# SEMAFORO VENCIMIENTO
# =========================
def estado_vencimiento(fecha):
    hoy = pd.Timestamp.today().normalize()
    dias = (fecha - hoy).days

    if dias <= 0:
        return "🔴 Urgente"
    elif dias <= 7:
        return "🟡 Próximo"
    else:
        return "🟢 A tiempo"

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

df_filtrado = df.copy()

df_filtrado = df_filtrado[
    (df_filtrado["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
    (df_filtrado["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

st.subheader(f"📋 Clientes encontrados: {len(df_filtrado)}")

# =========================
# EXPORTAR EXCEL
# =========================
def convertir_excel(dataframe):
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    return buffer.getvalue()

st.download_button(
    "⬇️ Descargar lista filtrada",
    convertir_excel(df_filtrado),
    "clientes_filtrados.xlsx"
)

# =========================
# WHATSAPP APP
# =========================
def abrir_whatsapp(nombre, placa, telefono, sede, fecha):

    telefono = str(telefono).replace(".0", "").replace(" ", "")

    if not telefono.startswith("57"):
        telefono = "57" + telefono

    fecha_txt = fecha.strftime("%d/%m/%Y")

    mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente {sede}.

Tu vehículo con placa {placa} vence su tecnomecánica el {fecha_txt}.

¿Deseas agendar tu revisión hoy? 🚗✅"""

    mensaje_codificado = urllib.parse.quote(mensaje)

    url = f"whatsapp://send?phone={telefono}&text={mensaje_codificado}"

    webbrowser.open(url)

# =========================
# LISTADO CLIENTES CRM
# =========================
estados_validos = ["Pendiente", "Contactado", "Agendado", "Renovado"]

for i, row in df_filtrado.iterrows():

    with st.container():

        col1, col2, col3, col4 = st.columns([2,2,2,2])

        col1.write(f"**🚘 {row['Placa']}**")
        col1.write(row["Cliente"])

        semaforo = estado_vencimiento(row["Fecha_Renovacion"])
        col2.write(f"📅 {row['Fecha_Renovacion'].date()} — {semaforo}")
        col2.write(f"🏢 {row['Sede']}")

        estado_actual = row["Estado"]
        if estado_actual not in estados_validos:
            estado_actual = "Pendiente"

        nuevo_estado = col3.selectbox(
            "Estado",
            estados_validos,
            index=estados_validos.index(estado_actual),
            key=f"estado_{i}"
        )

        if nuevo_estado != estado_actual:
            st.session_state.df.loc[i, "Estado"] = nuevo_estado
            st.rerun()

        if col4.button("📲 WhatsApp", key=f"wp_{i}"):
            abrir_whatsapp(
                row["Cliente"],
                row["Placa"],
                row["Telefono"],
                row["Sede"],
                row["Fecha_Renovacion"]
            )

    st.divider()

# =========================
# GUARDAR CAMBIOS
# =========================
if st.button("💾 Guardar cambios"):
    st.session_state.df.to_excel(ARCHIVO, index=False)
    st.success("✅ Cambios guardados correctamente")
