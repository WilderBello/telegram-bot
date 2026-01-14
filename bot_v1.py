import io, pdfplumber, requests, os
from telegram.ext import Updater, MessageHandler, Filters
from etl import *
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = [int(u) for u in os.getenv("ALLOWED_USERS", "").split(",") if u]

def read_pdf(update, context):
    message = update.message
    user_id = message.from_user.id

    # Verificacion de usuario
    if user_id not in ALLOWED_USERS:
        message.reply_text("❌ No estás autorizado para usar este bot.")
        return
    
    # Verifica si hay documento adjunto
    if message.document and message.document.mime_type == "application/pdf":
        file = context.bot.get_file(message.document.file_id)
        file_bytes = io.BytesIO(requests.get(file.file_path).content)

        try:
            datos, fecha_str = Procesar_PDF(file_bytes)
            message.reply_text(f"Los datos corresponden a la fecha: {fecha_str}")
            archivo_ics = Carga_ics(datos, fecha_str)
            message.reply_document(document=archivo_ics, filename=f"Eventos_{fecha_str}.ics", caption=f"Info del mes: {fecha_str}\n 📅 Archivo .ics generado correctamente.")
            message.reply_text("✅ PDF procesado correctamente.")

        except Exception as e:
            message.reply_text(f"❌ Error al leer el PDF: {e}")
    else:
        message.reply_text("Por favor envíame un archivo PDF 📄")

def main():
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Escucha cualquier mensaje que contenga un documento
    dp.add_handler(MessageHandler(Filters.document, read_pdf))

    # Inicia el bot
    print("🤖 Bot escuchando...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()