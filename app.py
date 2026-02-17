import streamlit as st
import pandas as pd
import urllib.parse
import os
import json
import shutil
import hashlib
from datetime import datetime

# ======================================================
# CONFIGURACIÓN
# ======================================================

st.set_page_config(page_title="CRM CDA", layout="wide")

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_BASES = "bases"

os.makedirs(CARPETA_BASES, exist_ok=True)

# ======================================================
# FUNCIONES DE USUARIOS
# ======================================================

def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def inicializar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS) or os.path.getsize(ARCHIVO_USUARIOS) == 0:
        with open(ARCHIVO_USUARIOS, "w") as f:
            json.dump({
                "admin": {
                    "password": hash_password("admin123"),
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
        pwd_hash = hash_password(pwd)

        if user in usuarios and usuarios[user]["password"] == pwd_hash:
            st.session_state.login = True
            st.session_state.usuario = user
            st.session_state.rol = usuarios[user]["rol"]
            st.experimental_rerun()
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
# CAMBIAR CONTRASEÑA
# ======================================================

st.subheader("🔑 Cambiar contraseña (opcional)")
nueva_pass_usuario = st.text_input("Nueva contraseña", type="password", key="new_pass_user")
if st.button("Actualizar contraseña"):
    if not nueva_pass_usuario.strip():
        st.error("La contraseña no puede estar vacía")
    else:
        usuarios = cargar_usuarios()
        usuarios[usuario_actual]["password"] = hash_password(nueva_pass_usuario)
        guardar_usuarios(usuarios)
        st.success("Contraseña actualizada correctamente")

# ======================================================
# CERRAR SESIÓN
# ======================================================

col_logout1, col_logout2 = st.columns([6,1])
with col_logout2:
    if st.button("🚪 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.experimental_rerun()

# ======================================================
# CARPETA USUARIO
# ======================================================

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
# FUNCIONES AUXILIARES
# ======================================================

def formatear_telefono(telefono):
    if pd.isna(telefono):
        return None
    telefono = str(telefono).replace(".0","").replace(" ","").replace("-","")
    if not telefono.startswith("57"):
        telefono = "57" + telefono
    return telefono

def link_whatsapp(nombre, placa, telefono, fecha):
    telefono = formatear_telefono(telefono)
    if not telefono:
        return None
    fecha_texto = fecha.strftime("%d/%m/%Y")
    mensaje = f"Hola {nombre}, soy Juan José 👋\nTu vehículo con placa {placa} vence el {fecha_texto}.\n¿Deseas agendar tu revisión? 🚗✅"
    mensaje = urllib.parse.quote(mensaje)
    return f"https://wa.me/{telefono}?text={mensaje}"

def link_llamada(telefono):
    telefono = formatear_telefono(telefono)
    if not telefono:
        return None
    return f"tel:+{telefono}"

# ======================================================
# CRM
# ======================================================

with tab_crm:

    st.sidebar.header("📂 Bases de Datos")

    archivo_subido = st.sidebar.file_uploader("Subir base Excel", type=["xlsx"])
    if archivo_subido:
        ruta_guardado = os.path.join(carpeta_usuario, archivo_subido.name)
        with open(ruta_guardado, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.sidebar.success("Base guardada correctamente")
        st.experimental_rerun()

    # Listado de bases
    bases_disponibles = []
    if rol_actual == "admin":
        for usuario in os.listdir(CARPETA_BASES):
            ruta_user = os.path.join(CARPETA_BASES, usuario)
            if not os.path.isdir(ruta_user):
                continue
            for archivo in os.listdir(ruta_user):
                if archivo.endswith(".xlsx"):
                    bases_disponibles.append((f"{usuario} - {archivo}", os.path.join(ruta_user, archivo)))
    else:
        for archivo in os.listdir(carpeta_usuario):
            if archivo.endswith(".xlsx"):
                bases_disponibles.append((archivo, os.path.join(carpeta_usuario, archivo)))

    if not bases_disponibles:
        st.warning("No hay bases cargadas")
        st.stop()

    nombres = [x[0] for x in bases_disponibles]
    seleccion = st.sidebar.selectbox("Seleccionar base", nombres)
    ARCHIVO = dict(bases_disponibles)[seleccion]

    # Eliminar base
    st.sidebar.divider()
    st.sidebar.subheader("🗑 Eliminar Base de Datos")
    if st.sidebar.button("Eliminar base seleccionada"):
        if st.confirm("¿Estás seguro de eliminar la base?"):
            try:
                os.remove(ARCHIVO)
                st.sidebar.success("Base eliminada correctamente")
                st.experimental_rerun()
            except Exception as e:
                st.sidebar.error(f"Error al eliminar la base: {e}")

    # ==================================================
    # CARGAR DATA
    # ==================================================
    try:
        df = pd.read_excel(ARCHIVO)
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.stop()

    df.columns = df.columns.str.strip()
    columnas_lower = {col.lower(): col for col in df.columns}
    posibles_fechas = ["fecha_renovacion","fecha","vencimiento","fecha vencimiento"]
    columna_fecha = next((columnas_lower[p] for p in posibles_fechas if p in columnas_lower), None)

    if columna_fecha is None:
        st.error("No se encontró columna de fecha")
        st.write("Columnas detectadas:", list(df.columns))
        st.stop()

    df.rename(columns={columna_fecha: "Fecha_Renovacion"}, inplace=True)
    df["Fecha_Renovacion"] = pd.to_datetime(df["Fecha_Renovacion"], errors="coerce", dayfirst=True)
    df = df[df["Fecha_Renovacion"].notna()]

    if "Estado" not in df.columns:
        df["Estado"] = "Pendiente"
    if "Sede" not in df.columns:
        df["Sede"] = "Sin sede"

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
    fecha_min = df["Fecha_Renovacion"].min()
    fecha_max = df["Fecha_Renovacion"].max()

    with col_f1:
        fecha_inicio = st.date_input("Desde", fecha_min.date())
    with col_f2:
        fecha_fin = st.date_input("Hasta", fecha_max.date())
    with col_f3:
        sedes = ["Todas"] + sorted(df["Sede"].dropna().astype(str).unique().tolist())
        sede_sel = st.selectbox("Sede", sedes)

    df_filtrado = df[(df["Fecha_Renovacion"] >= pd.Timestamp(fecha_inicio)) &
                     (df["Fecha_Renovacion"] <= pd.Timestamp(fecha_fin))]
    if sede_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Sede"] == sede_sel]

    st.divider()

    # ==================================================
    # TABLA INTERACTIVA
    # ==================================================
    estados = ["Pendiente","Agendado","Renovado"]

    for i,row in df_filtrado.iterrows():
        col1,col2,col3,col4 = st.columns(4)
        col1.write(f"**{row.get('Placa','')}**")
        col1.write(row.get("Cliente",""))
        col2.write(row["Fecha_Renovacion"].date())

        # Estado
        estado_actual = row["Estado"]
        estado = col3.selectbox("Estado", estados, index=estados.index(estado_actual), key=f"estado_{i}")
        if estado != estado_actual:
            df.loc[i,"Estado"] = estado
            df.to_excel(ARCHIVO, index=False)
            st.experimental_rerun()

        # WhatsApp y Llamada
        if "Telefono" in df.columns:
            url_whatsapp = link_whatsapp(row.get("Cliente",""), row.get("Placa",""), row.get("Telefono",""), row["Fecha_Renovacion"])
            url_llamada = link_llamada(row.get("Telefono",""))

            if url_whatsapp:
                col4.markdown(
                    f'<a href="{url_whatsapp}" target="_blank">'
                    f'<button style="width:100%;padding:8px;border-radius:8px;background-color:#25D366;color:white;border:none;">📲 WhatsApp</button></a>',
                    unsafe_allow_html=True
                )
            if url_llamada:
                col4.markdown(
                    f'<a href="{url_llamada}">'
                    f'<button style="width:100%;padding:8px;border-radius:8px;background-color:#1f77b4;color:white;border:none;">📞 Llamar</button></a>',
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
            elif not nuevo_user.strip() or not nueva_pass.strip():
                st.error("Campos vacíos")
            else:
                usuarios[nuevo_user] = {"password": hash_password(nueva_pass), "rol": "usuario"}
                guardar_usuarios(usuarios)
                os.makedirs(os.path.join(CARPETA_BASES,nuevo_user),exist_ok=True)
                st.success("Usuario creado correctamente")
                st.experimental_rerun()

        st.divider()
        st.subheader("Usuarios registrados")
        for user,datos in usuarios.items():
            col1,col2,col3,col4 = st.columns([3,2,2,1])
            col1.write(f"👤 {user} ({datos['rol']})")

            with st.expander("🔑 Ver / modificar contraseña"):
                st.write("Por seguridad, las contraseñas están encriptadas")
                nueva_pass_admin = st.text_input(f"Nueva contraseña para {user}", type="password", key=f"pass_{user}")
                if st.button(f"Actualizar contraseña {user}", key=f"update_{user}"):
                    if not nueva_pass_admin.strip():
                        st.error("La contraseña no puede estar vacía")
                    else:
                        usuarios[user]["password"] = hash_password(nueva_pass_admin)
                        guardar_usuarios(usuarios)
                        st.success(f"Contraseña de {user} actualizada")
                        st.experimental_rerun()

            if user != "admin":
                if st.button("🗑 Eliminar", key=f"del_{user}"):
                    if st.confirm(f"¿Seguro quieres eliminar al usuario {user}?"):
                        del usuarios[user]
                        guardar_usuarios(usuarios)
                        carpeta_eliminar = os.path.join(CARPETA_BASES,user)
                        if os.path.exists(carpeta_eliminar):
                            shutil.rmtree(carpeta_eliminar)
                        st.success("Usuario eliminado")
                        st.experimental_rerun()

