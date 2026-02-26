import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import urllib.parse
import os
import json
import plotly.express as px

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(page_title="CRM CDA PRO", layout="wide")

DB = "crm.db"
ARCHIVO_USUARIOS = "usuarios.json"

# ======================================================
# SEGURIDAD PASSWORD HASH
# ======================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ======================================================
# BASE DE DATOS
# ======================================================

def conectar_db():
    return sqlite3.connect(DB, check_same_thread=False)

def crear_tablas():
    conn = conectar_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        cliente TEXT,
        placa TEXT,
        telefono TEXT,
        sede TEXT,
        fecha_renovacion TEXT,
        estado TEXT
    )
    """)

    conn.commit()
    conn.close()

crear_tablas()

# ======================================================
# USUARIOS
# ======================================================

def inicializar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS,"w") as f:
            json.dump({
                "admin":{
                    "password":hash_password("admin123"),
                    "rol":"admin"
                }
            },f,indent=4)

def cargar_usuarios():
    with open(ARCHIVO_USUARIOS,"r") as f:
        return json.load(f)

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS,"w") as f:
        json.dump(data,f,indent=4)

inicializar_usuarios()

# ======================================================
# SESSION
# ======================================================

if "login" not in st.session_state:
    st.session_state.login=False
    st.session_state.usuario=None
    st.session_state.rol=None

# ======================================================
# LOGIN
# ======================================================

def pantalla_login():
    st.title("🔐 CRM CDA PRO")

    user=st.text_input("Usuario")
    pwd=st.text_input("Contraseña",type="password")

    if st.button("Ingresar"):
        usuarios=cargar_usuarios()

        if user in usuarios and usuarios[user]["password"]==hash_password(pwd):
            st.session_state.login=True
            st.session_state.usuario=user
            st.session_state.rol=usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.login:
    pantalla_login()
    st.stop()

usuario_actual=st.session_state.usuario
rol_actual=st.session_state.rol

st.title("🚗 CRM Renovaciones CDA")
st.write(f"👤 {usuario_actual} | Rol: {rol_actual}")

if st.button("🚪 Cerrar sesión"):
    st.session_state.login=False
    st.rerun()

# ======================================================
# TABS
# ======================================================

tabs=["📊 CRM"]

if rol_actual=="admin":
    tabs+=["👑 Administración","📈 Dashboard"]

tab_objs=st.tabs(tabs)
tab_crm=tab_objs[0]

# ======================================================
# ================= CRM =================
# ======================================================

with tab_crm:

    st.sidebar.header("📂 Importar Excel")

    archivo=st.sidebar.file_uploader("Subir base",type=["xlsx"])

    # ==================================================
    # IMPORTAR EXCEL → SQLITE
    # ==================================================

    if archivo:

        df=pd.read_excel(archivo)
        df.columns=df.columns.str.strip()

        columnas_lower={c.lower():c for c in df.columns}

        posibles=["fecha_renovacion","fecha","vencimiento","fecha vencimiento"]

        col_fecha=None
        for p in posibles:
            if p in columnas_lower:
                col_fecha=columnas_lower[p]
                break

        if col_fecha is None:
            st.error("No se encontró columna fecha")
        else:

            df.rename(columns={col_fecha:"Fecha_Renovacion"},inplace=True)

            df["Fecha_Renovacion"]=pd.to_datetime(
                df["Fecha_Renovacion"],
                errors="coerce",
                dayfirst=True
            )

            df["Estado"]="Pendiente"

            conn=conectar_db()

            for _,row in df.iterrows():
                conn.execute("""
                INSERT INTO clientes
                (usuario,cliente,placa,telefono,sede,fecha_renovacion,estado)
                VALUES (?,?,?,?,?,?,?)
                """,(
                    usuario_actual,
                    str(row.get("Cliente","")),
                    str(row.get("Placa","")),
                    str(row.get("Telefono","")),
                    str(row.get("Sede","Sin sede")),
                    str(row["Fecha_Renovacion"].date()),
                    "Pendiente"
                ))

            conn.commit()
            conn.close()

            st.success("Base importada a la base de datos 🚀")
            st.rerun()

    # ==================================================
    # CARGAR DATA
    # ==================================================

    conn=conectar_db()

    if rol_actual=="admin":
        df=pd.read_sql("SELECT * FROM clientes",conn)
    else:
        df=pd.read_sql(
            "SELECT * FROM clientes WHERE usuario=?",
            conn,
            params=(usuario_actual,)
        )

    conn.close()

    if df.empty:
        st.warning("No hay datos")
        st.stop()

    df["fecha_renovacion"]=pd.to_datetime(df["fecha_renovacion"])

    # ==================================================
    # METRICAS
    # ==================================================

    c1,c2,c3,c4=st.columns(4)

    c1.metric("Total",len(df))
    c2.metric("Pendientes",(df.estado=="Pendiente").sum())
    c3.metric("Agendados",(df.estado=="Agendado").sum())
    c4.metric("Renovados",(df.estado=="Renovado").sum())

    st.divider()

    # ==================================================
    # WHATSAPP
    # ==================================================

    def link_whatsapp(nombre,placa,telefono,fecha):

        telefono=str(telefono).replace(".0","")

        if not telefono.startswith("57"):
            telefono="57"+telefono

        mensaje=f"""Hola {nombre}, soy Juan José Mestra asesor CDA 👋

Tu vehículo {placa} vence el {fecha.strftime('%d/%m/%Y')}

¿Deseas agendar tu revisión? 🚗✅"""

        return f"https://wa.me/{telefono}?text={urllib.parse.quote(mensaje)}"

    estados=["Pendiente","Agendado","Renovado"]

    conn=conectar_db()

    for _,row in df.iterrows():

        col1,col2,col3,col4=st.columns(4)

        col1.write(f"**{row.placa}**")
        col1.write(row.cliente)

        col2.write(row.fecha_renovacion.date())

        nuevo_estado=col3.selectbox(
            "Estado",
            estados,
            index=estados.index(row.estado),
            key=f"estado_{row.id}"
        )

        if nuevo_estado!=row.estado:
            conn.execute(
                "UPDATE clientes SET estado=? WHERE id=?",
                (nuevo_estado,row.id)
            )
            conn.commit()
            st.rerun()

        url=link_whatsapp(
            row.cliente,
            row.placa,
            row.telefono,
            row.fecha_renovacion
        )

        col4.markdown(
            f'<a href="{url}" target="_blank">'
            f'<button style="width:100%;background:#25D366;color:white;padding:8px;border:none;border-radius:8px;">📲 WhatsApp</button></a>',
            unsafe_allow_html=True
        )

        col4.markdown(
            f'<a href="tel:+57{row.telefono}">'
            f'<button style="width:100%;background:#1f77b4;color:white;padding:8px;border:none;border-radius:8px;">📞 Llamar</button></a>',
            unsafe_allow_html=True
        )

        st.divider()

    conn.close()

# ======================================================
# ADMIN
# ======================================================

if rol_actual=="admin":

    with tab_objs[1]:

        st.header("👑 Administración")

        usuarios=cargar_usuarios()

        nuevo=st.text_input("Nuevo usuario")
        pwd=st.text_input("Contraseña",type="password")

        if st.button("Crear usuario"):
            usuarios[nuevo]={
                "password":hash_password(pwd),
                "rol":"usuario"
            }
            guardar_usuarios(usuarios)
            st.success("Usuario creado")
            st.rerun()

# ======================================================
# DASHBOARD
# ======================================================

if rol_actual=="admin":

    with tab_objs[2]:

        st.header("📈 Dashboard Visual")

        conteo=df.estado.value_counts().reindex(
            ["Pendiente","Agendado","Renovado"],
            fill_value=0
        )

        fig_bar=px.bar(
            x=conteo.index,
            y=conteo.values,
            text=conteo.values
        )

        st.plotly_chart(fig_bar)

        fig_pie=px.pie(
            names=conteo.index,
            values=conteo.values
        )

        st.plotly_chart(fig_pie)
