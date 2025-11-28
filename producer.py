import time
import json
import requests
import os
from kafka import KafkaProducer
from datetime import datetime
import pytz

# 1. Configuración de Kafka desde variables de entorno
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
API_URL = os.getenv('API_URL', 'http://100.111.193.44:8001/health/')

# Configuración de zona horaria de Chile
CHILE_TZ = pytz.timezone('America/Santiago')

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

TOPIC_NAME = 'eventos_raw'

print(f"Iniciando monitor de {API_URL} hacia Kafka...")

while True:
    try:
        # Tomamos el tiempo antes de la petición
        start_time = time.time()
        
        # Hacemos el PING real a tu App
        response = requests.get(API_URL, timeout=5)
        
        # Calculamos latencia (tiempo que tardó en responder) en milisegundos
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Armamos el mensaje para Kafka
        data = {
            "timestamp": datetime.now(CHILE_TZ).isoformat(),
            "url": API_URL,
            "status_code": response.status_code, # Será 200 o 503 según tu lógica
            "latency_ms": latency_ms,
            "db_status": response.json().get('database', 'unknown') # Extraemos info del JSON
        }

        # Enviamos a Kafka
        producer.send(TOPIC_NAME, value=data)
        print(f"Enviado: {data['status_code']} - {latency_ms}ms")

    except requests.exceptions.ConnectionError:
        data = {
            "timestamp": datetime.now(CHILE_TZ).isoformat(),
            "url": API_URL,
            "status_code": 0, # Indica que no hubo respuesta
            "latency_ms": 0,
            "db_status": "disconnected"
        }
        producer.send(TOPIC_NAME, value=data)
        print("Error: La App no responde (ConnectionError)")

    except Exception as e:
        print(f"Error inesperado en el script: {e}")

    # Esperar 1 segundo antes del siguiente ping
    time.sleep(1)