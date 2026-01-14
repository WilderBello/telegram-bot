# Nota: 
* Es necesario el entorno pipenv.
* 

# Ejecución
* crear la carpeta: `json` e incluir `horarios_base.json`
* Ejecutar: `docker-compose up -d --build`

## Estructura general:
* bot_v1: Es el archivo principal a ejecutar, contiene la estructura del bot.
* ETL: Extrae, Transforma y Carga los datos del PDF y los json.

## La estructura contiene las siguientes carpetas adicionales:

* json: Se almacenan todos los datos en formato json con la estructura:
```json
  {
    "evento": {
        "summary": "Nombre evento",
        "hora_start": "07:00:00", # Hora de inicio
        "hora_end": "07:30:00", # Hora de finalizacion
        "color": "5" # color del evento en Calendar
    },
  }
  ```
