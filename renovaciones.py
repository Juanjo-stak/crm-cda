import pandas as pd
from datetime import datetime
import urllib.parse

df = pd.read_excel("clientes.xlsx")
df.columns = df.columns.str.strip()

df["fecca"] = pd.to_datetime(df["fecca"])

hoy = datetime.today()
df["Dias_para_vencer"] = (df["fecca"] - hoy).dt.days

alertas = df[(df["Dias_para_vencer"].isin([30, 15, 5])) | (df["Dias_para_vencer"] < 0)]

def crear_mensaje(cliente):
    dias = cliente["Dias_para_vencer"]
    if dias < 0:
        estado = "YA VENCIDO"
    else:
        estado = f"vence en {dias} días"
        
    mensaje = f"Hola {cliente['Cliente']}, tu revisión técnico mecánica del vehículo {cliente['Placa']} {estado}. Agenda tu renovación con nosotros y evita multas."
    return mensaje

alertas["Mensaje"] = alertas.apply(crear_mensaje, axis=1)

# Agregar prefijo Colombia
alertas["Telefono_WA"] = "57" + alertas["Telefono"].astype(str)

# Codificar mensaje para URL
alertas["Mensaje_URL"] = alertas["Mensaje"].apply(lambda x: urllib.parse.quote(x))

# Crear link WhatsApp
alertas["Link_WhatsApp"] = (
    "https://wa.me/" + alertas["Telefono_WA"] + "?text=" + alertas["Mensaje_URL"]
)

nombre_archivo = f"clientes_para_contactar_{hoy.strftime('%Y-%m-%d')}.xlsx"
alertas.to_excel(nombre_archivo, index=False)

print(f"\nArchivo generado: {nombre_archivo}")
print("Listo para hacer clic y enviar 🚀")


