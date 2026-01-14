# Usar Python 3.10.11 slim
FROM python:3.10.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar Pipfile y Pipfile.lock
COPY Pipfile Pipfile.lock /app/

# Instalar pipenv y dependencias
RUN pip install --no-cache-dir pipenv \
    && pipenv install --deploy --ignore-pipfile

# Copiar el resto del código
COPY . /app
# Variables de entorno para que Python no haga buffering
ENV PYTHONUNBUFFERED=1

# Ejecutar el bot
CMD ["pipenv", "run", "python", "bot_v1.py"]
