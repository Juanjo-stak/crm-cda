import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import plotly.express as px  # Para gráficos interactivos

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
# 🔴 AGREGADO: CERRAR SESIÓN
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
# =========================
# KPI PROFESIONAL VERTICAL
# =========================

st.subheader("📊 Métricas Generales")

total = len(df)
pendientes = (df["Estado"]=="Pendiente").sum()
agendados = (df["Estado"]=="Agendado").sum()
renovados = (df["Estado"]=="Renovado").sum()

st.markdown(f"""
<div style="
    background-color:#1f2937;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Total Registros</h3>
    <h1 style="font-size:40px;">{total}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#7f1d1d;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Pendientes</h3>
    <h1 style="font-size:40px;">{pendientes}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#92400e;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Agendados</h3>
    <h1 style="font-size:40px;">{agendados}</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    background-color:#065f46;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    text-align:center;
    color:white;">
    <h3>Renovados</h3>
    <h1 style="font-size:40px;">{renovados}</h1>
</div>
""", unsafe_allow_html=True)

st.divider()

# ======================================================
# TABS
# ======================================================

tabs_lista = ["📊 CRM"]
if rol_actual == "admin":
    tabs_lista.append("👑 Panel Administración")
    tabs_lista.append("📈 Dashboard Visual")  # Nueva pestaña

tabs_objs = st.tabs(tabs_lista)

# Asignar objetos a variables según rol
tab_crm = tabs_objs[0]
if rol_actual == "admin":
    tab_admin = tabs_objs[1]
    tab_dashboard = tabs_objs[2]

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
    # DASHBOARD
    # ==================================================

    st.markdown("## 📊 Dashboard")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Total", len(df))
    c2.metric("Pendientes", (df["Estado"]=="Pendiente").sum())
    c3.metric("Agendados", (df["Estado"]=="Agendado").sum())
    c4.metric("Renovados", (df["Estado"]=="Renovado").sum())

    st.divider()

    # ==================================================
    # FILTROS
    # ==================================================

    st.markdown("## 🔎 Filtros")

    col_f1, col_f2, col_f3 = st.columns(3)

    if "Sede" not in df.columns:
        df["Sede"] = "Sin sede"

    fecha_min = df["Fecha_Renovacion"].min()
    fecha_max = df["Fecha_Renovacion"].max()

    with col_f1:
        fecha_inicio = st.date_input("Desde", fecha_min.date())

    with col_f2:
        fecha_fin = st.date_input("Hasta", fecha_max.date())

    with col_f3:
        sedes = ["Todas"] + sorted(df["Sede"].dropna().astype(str).unique().tolist())
        sede_sel = st.selectbox("Sede", sedes)

    df_filtrado = df[
        (df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
        (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))
    ]

    if sede_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

    st.divider()

    # ==================================================
    # WHATSAPP & LLAMAR
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

    estados = ["Pendiente","Agendado","Renovado"]

    for i,row in df_filtrado.iterrows():

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
                            cursor:pointer;">
                            📲 WhatsApp
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

            # 📞 BOTÓN LLAMAR
            telefono = str(row.get("Telefono","")).replace(".0","").replace(" ","").replace("-","")
            if telefono:
                if not telefono.startswith("57"):
                    telefono = "57" + telefono
                link_llamada = f"tel:+{telefono}"
                col4.markdown(
                    f'<a href="{link_llamada}">'
                    f'<button style="width:100%;padding:8px;'
                    f'border-radius:8px;background-color:#1f77b4;'
                    f'color:white;border:none;">📞 Llamar</button></a>',
                    unsafe_allow_html=True
                )

        st.divider()

# ======================================================
# PANEL ADMIN
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

            col1,col2,col3 = st.columns([3,2,1])
            col1.write(f"👤 {user} ({datos['rol']})")
            col2.write(f"🔑 {datos['password']}")  # ✅ Mostrar contraseña

            if user != "admin":
                if col3.button("🗑 Eliminar", key=f"del_{user}"):
                    del usuarios[user]
                    guardar_usuarios(usuarios)
                    carpeta_eliminar = os.path.join(CARPETA_BASES,user)
                    if os.path.exists(carpeta_eliminar):
                        shutil.rmtree(carpeta_eliminar)
                    st.success("Usuario eliminado")
                    st.rerun()

# ======================================================
# TAB DASHBOARD VISUAL (SOLO ADMIN)
# ======================================================

if rol_actual == "admin":

    with tab_dashboard:

        st.header("📈 Dashboard Visual de Estados")

        if not bases_disponibles:
            st.warning("No hay bases cargadas")
        else:
            # Contar estados
            conteo_estados = df["Estado"].value_counts().reindex(["Pendiente","Agendado","Renovado"], fill_value=0)

            # ====== Gráfico de barras cuadrado ======
            st.subheader("Gráfico de barras de Estados")
            fig_bar = px.bar(
                x=conteo_estados.index,
                y=conteo_estados.values,
                text=conteo_estados.values,
                width=400,  # ancho cuadrado
                height=400, # alto cuadrado
                color=conteo_estados.index,
                color_discrete_map={
                    "Pendiente":"red",
                    "Agendado":"yellow",
                    "Renovado":"green"
                }
            )
            fig_bar.update_layout(
                showlegend=False,
                yaxis_title="Cantidad",
                xaxis_title="Estado",
                margin=dict(l=20,r=20,t=30,b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=False)

            # ====== Gráfico de pastel cuadrado ======
            st.subheader("Gráfico de pastel de Estados")
            fig_pie = px.pie(
                names=conteo_estados.index,
                values=conteo_estados.values,
                title="Proporción de Estados",
                width=400,
                height=400,
                color=conteo_estados.index,
                color_discrete_map={
                    "Pendiente":"red",
                    "Agendado":"yellow",
                    "Renovado":"green"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=False)

            # ====== DESCARGA DE DATOS ======
            st.subheader("💾 Descargar datos filtrados")
            
            # CSV
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='datos_filtrados.csv',
                mime='text/csv'
            )

            # Excel
            excel_path = "datos_filtrados.xlsx"
            df_filtrado.to_excel(excel_path, index=False)
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="Descargar Excel",
                    data=f,
                    file_name="datos_filtrados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

