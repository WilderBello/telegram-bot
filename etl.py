import os, json, pdfplumber, re, uuid
import pandas as pd
from ics import Calendar, Event
from io import BytesIO
from datetime import datetime, timedelta

#######  ETL depurada para proyecto de BOT en Telegram.

####### Extraction - Extraccion de los datos

# Traduccion de aleman a ingles para la fecha en pandas - PDF en aleman.
def traducir_mes_aleman(mes_str):
    traducciones = {
        "Januar": "January",
        "Februar": "February",
        "März": "March",
        "Mai": "May",
        "Juni": "June",
        "Juli": "July",
        "Oktober": "October",
        "Dezember": "December"
    }

    for aleman, ingles in traducciones.items():
        if aleman in mes_str:
            return mes_str.replace(aleman, ingles)
    
    return mes_str

# Seleccion de formato de datos - Existen 2 tipos de PDF hasta el momento 
def Problema_Fecha(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_table()
    
    try:
        # PDF de Noviembre 2024
        df_plumber = pd.DataFrame(table[1:], columns=table[0]).drop(columns=[table[0][0]])  # Elimina primera columna
        # Fecha en string
        fecha_str = df_plumber.iloc[0, 0].replace("\n", " ")
        # Limpiar el DataFrame eliminando la primera fila y columna innecesaria
        df_plumber = df_plumber.iloc[1:, 1:].reset_index(drop=True)
        # Traducir mes si está en alemán
        fecha_str = traducir_mes_aleman(fecha_str)
        fecha = pd.to_datetime(fecha_str, format="%B %Y", errors="coerce")

        if pd.isna(fecha):
            raise ValueError("La conversión de fecha dio como resultado NaT")

    except Exception as e:
        # PDF de Abril 2025
        df_plumber = pd.DataFrame(table[1:], columns=table[0])
        # Eliminando las ultimas 4 columnas
        df_plumber = df_plumber.iloc[:,:-4]
        # Fecha en string
        fecha_str = df_plumber.columns[0].replace("\n", " ")
        # Eliminando dos primeras filas
        df_plumber = df_plumber.iloc[:, 2:].reset_index(drop=True)
        # Traducir mes si está en alemán
        fecha_str = traducir_mes_aleman(fecha_str)
        fecha = pd.to_datetime(fecha_str, format="%B %Y")

    return df_plumber, fecha, fecha_str

####### Transform - Transformacion de los datos

# Función para verificar y modificar el formato de las celdas
def modificar_celda(valor):
    if isinstance(valor, str) and '\n' in valor:
        lineas = [x.strip().lower() for x in valor.split('\n')]
        if len(lineas) > 2 and 'fb' in lineas:
            return f'{lineas[1]}-{lineas[lineas.index("fb")]}'
        elif len(lineas) == 2:
            return lineas[1] if 'f' in lineas else f'{lineas[0]}-{lineas[1]}'
    return valor  # Retorna el valor original si no cumple las condiciones

# Transformar datos a dataframe
def Procesar_PDF(pdf_path="GGZ Intranet.pdf"):
    df_plumber, fecha, fecha_str = Problema_Fecha(pdf_path)

    # Establecer nombres de columnas y eliminar columnas vacías
    df_plumber.columns = df_plumber.iloc[0]
    df_plumber = df_plumber.loc[:, df_plumber.columns.notna() & (df_plumber.columns != '')]

    # Convertir la primera fila en fechas sin hora
    df_plumber.loc[0, :] = pd.to_datetime([f"{fecha.year}-{fecha.month:02d}-{dia}" for dia in df_plumber.columns]).date

    # Eliminar segunda fila
    df_plumber = df_plumber.drop(index=1).reset_index(drop=True)

    # Mantener solo las dos primeras filas
    df_plumber = df_plumber.head(2).reset_index(drop=True)

    # Verificar si hay saltos de línea antes de aplicar modificaciones
    if df_plumber.map(lambda x: isinstance(x, str) and '\n' in x).any().any():
        df_plumber = df_plumber.map(modificar_celda)

    # Convertir segunda fila a minúsculas
    df_plumber.loc[1, :] = df_plumber.loc[1, :].astype(str).str.lower()

    # Exportar a CSV
    # df_plumber.to_csv("Horario_en_excel.csv", index=False)
    
    return df_plumber, fecha_str

####### Load 
###Carga de archivo json
def Carga_JSON():
    datos_cargados = {}
    archivos = ["horarios_base"]

    for archivo in archivos:
        archivo_json = f'./json/{archivo}.json'
        if os.path.exists(archivo_json):  # Verifica si el archivo existe antes de abrirlo
            try:
                with open(archivo_json, 'r', encoding='utf-8') as archivo_data:
                    datos_cargados[archivo] = json.load(archivo_data)
            except json.JSONDecodeError:
                print(f"Error al leer {archivo_json}: JSON mal formado.")
    
    return datos_cargados

### Carga de los datos a .ics
def Carga_ics(dataframe, fecha_str):
    CRLF = "\r\n"

    horarios_json = Carga_JSON().get("horarios_base", {})
    eventos = []

    for columna in dataframe.columns:
        fecha = dataframe.iloc[0][columna]
        titulo = dataframe.iloc[1][columna]

        eventualidad = horarios_json.get(titulo, horarios_json['desconocido'])

        # Limpiar saltos de línea en summary
        summary = re.sub(r'[\n\r]', '', f"{eventualidad['summary']} - {titulo}")

        # Horas
        hora_inicio = datetime.strptime(eventualidad['hora_start'], "%H:%M:%S").time()
        hora_fin = datetime.strptime(eventualidad['hora_end'], "%H:%M:%S").time()

        dt_inicio = datetime.combine(fecha, hora_inicio)
        dt_fin = datetime.combine(fecha, hora_fin)

        evento = (
            "BEGIN:VEVENT" + CRLF +
            f"UID:{uuid.uuid4()}@pdftocal.local" + CRLF +
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}" + CRLF +
            f"DTSTART;TZID=Europe/Vienna:{dt_inicio.strftime('%Y%m%dT%H%M%S')}" + CRLF +
            f"DTEND;TZID=Europe/Vienna:{dt_fin.strftime('%Y%m%dT%H%M%S')}" + CRLF +
            f"SUMMARY:{summary}" + CRLF +
            "END:VEVENT" + CRLF
        )

        eventos.append(evento)

    ics_content = (
        "BEGIN:VCALENDAR" + CRLF +
        "VERSION:2.0" + CRLF +
        "PRODID:-//PDFtoCAL//Telegram Bot//ES" + CRLF +
        "CALSCALE:GREGORIAN" + CRLF +

        "BEGIN:VTIMEZONE" + CRLF +
        "TZID:Europe/Vienna" + CRLF +

        "BEGIN:STANDARD" + CRLF +
        "DTSTART:20231029T030000" + CRLF +
        "TZOFFSETFROM:+0200" + CRLF +
        "TZOFFSETTO:+0100" + CRLF +
        "TZNAME:CET" + CRLF +
        "END:STANDARD" + CRLF +

        "BEGIN:DAYLIGHT" + CRLF +
        "DTSTART:20240331T020000" + CRLF +
        "TZOFFSETFROM:+0100" + CRLF +
        "TZOFFSETTO:+0200" + CRLF +
        "TZNAME:CEST" + CRLF +
        "END:DAYLIGHT" + CRLF +

        "END:VTIMEZONE" + CRLF +
        "".join(eventos) +
        "END:VCALENDAR" + CRLF
    )

    ics_bytes = BytesIO()
    ics_bytes.write(ics_content.encode("utf-8"))
    ics_bytes.seek(0)

    print("✅ Archivo .ics generado correctamente y compatible con Android.")
    return ics_bytes
