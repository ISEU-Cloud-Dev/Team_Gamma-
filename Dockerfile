FROM python:3.11-alpine

WORKDIR /code

# Instalar dependencias del sistema necesarias para compilar ciertas librerías (como psycopg2 si es necesario)
RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

# Comando para ejecutar uvicorn apuntando a main dentro de app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]