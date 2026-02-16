import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# =========================
# CONFIGURACION PAGINA
# =========================
st.set_page_config(page_title="CRM CDA", layout="wide")

st.title("🚗 CRM Renovaciones CDA")

# =========================
# CARGAR BASE DE DATOS
# =========================
ARCHIVO = "clientes.xlsx"

@st.cache_data
def cargar_datos():
    df = pd.read_excel(ARCHIVO)

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

    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    return df


df = cargar_datos()

st.success("✅ Base cargada correctamente")

# =========================
# DASHBOARD DINAMICO
# =========================
st.markdown("## 📊 Dashboard Comercial")

total = len(df)
pendientes = len(df[df["Estado"]=="Pendiente"])
contactados = len(df[df["Estado"]=="Contactado"])
agendados = len(df[df["Estado"]=="Agendado"])
renovados = len(df[df["Estado"]=="Renovado"])

c1,c2,c3,c4,c5 = st.columns(5)

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
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False)
    return buffer.getvalue()

st.download_button(
    "⬇️ Descargar lista filtrada",
    convertir_excel(df_filtrado),
    "clientes_filtrados.xlsx"
)

# =========================
# GENERAR LINK WHATSAPP
# =========================
def generar_link_whatsapp(nombre, placa, telefono, sede, fecha):

    telefono = str(telefono).replace(".0","").replace(" ","")

    if not telefono.startswith("57"):
        telefono = "57" + telefono

    # ===== FORMATO FECHA EN ESPAÑOL =====
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    meses = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","septiembre","octubre","noviembre","diciembre"
    ]

    fecha_texto = f"{dias[fecha.weekday()]} {fecha.day} de {meses[fecha.month-1]} de {fecha.year}"

    mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente {sede}.

Tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión hoy? """

    mensaje_codificado = urllib.parse.quote(mensaje)

    return f"https://api.whatsapp.com/send?phone={telefono}&text={mensaje_codificado}"


# =========================
# LISTADO CLIENTES CRM
# =========================
estados_validos = ["Pendiente","Contactado","Agendado","Renovado"]

for i, row in df_filtrado.iterrows():

    with st.container():

        col1,col2,col3,col4 = st.columns([2,2,2,2])

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

        df.loc[i,"Estado"] = nuevo_estado

        link_wp = generar_link_whatsapp(
            row["Cliente"],
            row["Placa"],
            row["Telefono"],
            row["Sede"],
            row["Fecha_Renovacion"]
        )

        col4.link_button("📲 WhatsApp", link_wp)

    st.divider()

# =========================
# GUARDAR CAMBIOS
# =========================
if st.button("💾 Guardar cambios"):
    df.to_excel(ARCHIVO, index=False)
    st.success("✅ Cambios guardados correctamente")
