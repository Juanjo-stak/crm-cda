import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import plotly.express as px

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
# TABS
# ======================================================

tabs_lista = ["📊 CRM"]
if rol_actual == "admin":
    tabs_lista += ["👑 Panel Administración", "📈 Dashboard Visual"]

tabs = st.tabs(tabs_lista)

# ======================================================
# FUNCION WHATSAPP (FINAL)
# ======================================================

def link_whatsapp(nombre, placa, telefono, fecha, sede):

    if pd.isna(telefono):
        return None

    telefono = str(telefono).replace(".0","").replace(" ","").replace("-","")

    if not telefono.startswith("57"):
        telefono = "57" + telefono

    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    meses = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]

    fecha_texto = f"{dias[fecha.weekday()]} {fecha.day} de {meses[fecha.month-1]} de {fecha.year}"

    mensaje = f"""Hola {nombre}, soy Juan José Mestra 👋

Te escribimos del CDA del Occidente — sede {sede}.

La revisión técnico mecánica de tu vehículo con placa {placa} vence el {fecha_texto}.

¿Deseas agendar tu revisión hoy? 🚗✅"""

    mensaje = urllib.parse.quote(mensaje)

    return f"https://wa.me/{telefono}?text={mensaje}"

# ======================================================
# ====================== CRM ===========================
# ======================================================

with tabs[0]:

    st.sidebar.header("📂 Bases de Datos")

    archivo_subido = st.sidebar.file_uploader("Subir base Excel", type=["xlsx"])

    if archivo_subido:
        ruta = os.path.join(carpeta_usuario, archivo_subido.name)
        with open(ruta, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("Base guardada")
        st.rerun()

    bases = []

    if rol_actual == "admin":
        for user in os.listdir(CARPETA_BASES):
            ruta_user = os.path.join(CARPETA_BASES, user)
            if os.path.isdir(ruta_user):
                for archivo in os.listdir(ruta_user):
                    if archivo.endswith(".xlsx"):
                        bases.append((f"{user} - {archivo}",
                                      os.path.join(ruta_user, archivo)))
    else:
        for archivo in os.listdir(carpeta_usuario):
            if archivo.endswith(".xlsx"):
                bases.append((archivo,
                              os.path.join(carpeta_usuario, archivo)))

    if not bases:
        st.warning("No hay bases cargadas")
        st.stop()

    seleccion = st.sidebar.selectbox(
        "Seleccionar base",
        [x[0] for x in bases]
    )

    ARCHIVO = dict(bases)[seleccion]
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

    # ================= CARGAR DATA =================

    df = pd.read_excel(ARCHIVO)
    df.columns = df.columns.str.strip()

    columnas_lower = {c.lower(): c for c in df.columns}

    posibles = ["fecha_renovacion","fecha","vencimiento","fecha vencimiento"]

    for p in posibles:
        if p in columnas_lower:
            df.rename(columns={columnas_lower[p]:"Fecha_Renovacion"}, inplace=True)
            break

    df["Fecha_Renovacion"] = pd.to_datetime(
        df["Fecha_Renovacion"],
        errors="coerce",
        dayfirst=True
    )

    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"

    if "Sede" not in df.columns:
        df["Sede"] = "Sin sede"

    # ================= DASHBOARD =================

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df["Estado"]=="Renovado").sum())

    st.divider()

    # ================= FILTROS =================

    col1,col2,col3 = st.columns(3)

    with col1:
        fecha_inicio = st.date_input("Desde", df["Fecha_Renovacion"].min().date())

    with col2:
        fecha_fin = st.date_input("Hasta", df["Fecha_Renovacion"].max().date())

    with col3:
        sedes = ["Todas"] + sorted(df["Sede"].astype(str).unique())
        sede_sel = st.selectbox("Sede", sedes)

    df_filtrado = df[
        (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
        (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
    ]

    if sede_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

    st.divider()

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
            key=f"estado_{i}"
        )

        if estado != row["Estado"]:
            df.loc[i,"Estado"] = estado
            df.to_excel(ARCHIVO, index=False)
            st.rerun()

        url = link_whatsapp(
            row.get("Cliente",""),
            row.get("Placa",""),
            row.get("Telefono",""),
            row["Fecha_Renovacion"],
            row.get("Sede","")
        )

        if url:
            col4.markdown(
                f'<a href="{url}" target="_blank">'
                f'<button style="width:100%;padding:10px;background:#25D366;color:white;border:none;border-radius:8px;">📲 WhatsApp</button></a>',
                unsafe_allow_html=True
            )

        telefono = str(row.get("Telefono","")).replace(".0","")
        if telefono:
            col4.markdown(
                f'<a href="tel:+57{telefono}">'
                f'<button style="width:100%;padding:8px;background:#1f77b4;color:white;border:none;border-radius:8px;">📞 Llamar</button></a>',
                unsafe_allow_html=True
            )

        st.divider()

# ======================================================
# PANEL ADMIN
# ======================================================

if rol_actual == "admin":

    with tabs[1]:

        st.header("👑 Panel Administración")

        usuarios = cargar_usuarios()

        nuevo_user = st.text_input("Nuevo usuario")
        nueva_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear Usuario"):
            if nuevo_user not in usuarios:
                usuarios[nuevo_user] = {
                    "password": nueva_pass,
                    "rol": "usuario"
                }
                guardar_usuarios(usuarios)
                os.makedirs(os.path.join(CARPETA_BASES,nuevo_user),exist_ok=True)
                st.success("Usuario creado")
                st.rerun()

        st.divider()

        for user,datos in usuarios.items():
            st.write(f"👤 {user} ({datos['rol']})")
            # ================= DASHBOARD PROFESIONAL =================

st.markdown("## 📊 Dashboard de Gestión")

total = len(df)

pendientes = (df["Estado"]=="Pendiente").sum()
agendados = (df["Estado"]=="Agendado").sum()
renovados = (df["Estado"]=="Renovado").sum()

contactados = agendados + renovados

# ===== Métricas principales =====
c1,c2,c3,c4 = st.columns(4)

c1.metric("Total Clientes", total)
c2.metric("Pendientes", pendientes)
c3.metric("Agendados", agendados)
c4.metric("Renovados", renovados)

st.divider()

# ===== Métricas comerciales =====

tasa_contacto = (contactados/total*100) if total else 0
tasa_agendamiento = (agendados/contactados*100) if contactados else 0
tasa_renovacion = (renovados/total*100) if total else 0

c5,c6,c7 = st.columns(3)

c5.metric("📞 Tasa Contacto", f"{tasa_contacto:.1f}%")
c6.metric("📅 Tasa Agendamiento", f"{tasa_agendamiento:.1f}%")
c7.metric("✅ Tasa Renovación", f"{tasa_renovacion:.1f}%")

st.divider()

# ===== Métricas de urgencia =====

hoy = pd.Timestamp.today().normalize()

vencen_hoy = (df["Fecha_Renovacion"] == hoy).sum()
proximos_7 = (
    (df["Fecha_Renovacion"] >= hoy) &
    (df["Fecha_Renovacion"] <= hoy + pd.Timedelta(days=7))
).sum()

c8,c9 = st.columns(2)

c8.metric("🚨 Vencen Hoy", vencen_hoy)
c9.metric("⏳ Próximos 7 días", proximos_7)

st.divider()
# ======================================================
# DASHBOARD GOOGLE ANALYTICS STYLE
# ======================================================

if rol_actual=="admin":

    with tabs[2]:

        st.header("📈 Dashboard Analítico")

        total=len(df)
        pendientes=(df["Estado"]=="Pendiente").sum()
        agendados=(df["Estado"]=="Agendado").sum()
        renovados=(df["Estado"]=="Renovado").sum()
        contactados=agendados+renovados

        c1,c2,c3,c4=st.columns(4)
        c1.metric("Total Clientes",total)
        c2.metric("Pendientes",pendientes)
        c3.metric("Agendados",agendados)
        c4.metric("Renovados",renovados)

        tasa_contacto=(contactados/total*100) if total else 0
        tasa_agenda=(agendados/contactados*100) if contactados else 0
        tasa_reno=(renovados/total*100) if total else 0

        c5,c6,c7=st.columns(3)
        c5.metric("📞 Tasa Contacto",f"{tasa_contacto:.1f}%")
        c6.metric("📅 Tasa Agendamiento",f"{tasa_agenda:.1f}%")
        c7.metric("✅ Tasa Renovación",f"{tasa_reno:.1f}%")

        st.divider()

        # ===== Grafico embudo ventas =====
        funnel_df=pd.DataFrame({
            "Etapa":["Pendientes","Contactados","Agendados","Renovados"],
            "Cantidad":[pendientes,contactados,agendados,renovados]
        })

        fig_funnel=px.funnel(funnel_df,x="Cantidad",y="Etapa",title="Embudo Comercial CDA")
        st.plotly_chart(fig_funnel,use_container_width=True)

        # ===== Renovaciones por día =====
        df["Dia"]=df["Fecha_Renovacion"].dt.date
        linea=df.groupby("Dia").size().reset_index(name="Clientes")

        fig_line=px.line(linea,x="Dia",y="Clientes",markers=True,
                         title="Clientes por Fecha de Vencimiento")

        st.plotly_chart(fig_line,use_container_width=True)
