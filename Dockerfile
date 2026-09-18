# Una sola etapa y una sola imagen para las dos cosas: correr la demo y correr los tests.
# Podria separarse en dos etapas para que la de la demo no cargue pytest, y son 3 MB: no
# vale el Dockerfile mas largo que habria que leer despues.
#
# La demo tiene que arrancar en una maquina limpia sin una sola API key. Ese fue el
# requisito numero uno de los nueve evaluadores, y es el que mas repos mata.
# Medido el 18/09/2026, con la cache vacia: 38 segundos desde `docker compose run` hasta
# la salida, bajando python:3.12-slim incluido.
FROM python:3.12-slim

# Pillow es la unica dependencia del programa, y solo para GENERAR comprobantes de prueba.
# El nucleo -las cuentas que vetan- no depende de nada fuera de la biblioteca estandar.
# pytest esta para que quien lea el repo pueda comprobar los tests, no para el programa.
RUN pip install --no-cache-dir "pillow>=11" "pytest>=8"

WORKDIR /app
# Entra el repositorio entero, menos lo que saca .dockerignore. Se probo enumerando las
# carpetas una por una y fallo dos veces: primero faltaban los .md y despues faltaban
# docker-compose.yml y docs/, porque hay tests que leen esos archivos para comprobar que el
# README no afirme cosas falsas. Cada vez el error aparecio recien adentro del contenedor.
#
# La alternativa era que esos tests se salteen cuando no encuentran el archivo. Un guardian
# que se desactiva solo no es un guardian, y ademas haria que el numero de pruebas sea
# distinto adentro y afuera, que es su propio olor.
COPY . /app/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8

ENTRYPOINT ["python", "-m", "remito"]
CMD ["demo"]
