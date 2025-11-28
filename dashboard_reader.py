import pandas as pd
import glob
import time
import os
from datetime import datetime, timedelta

# CONFIGURACIÓN
LAKE_DIR = "./datalake/lake2_metrics"
# Patrón para comprobar si hay archivos antes de intentar leer
SEARCH_PATTERN = os.path.join(LAKE_DIR, "*.parquet")

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

print(f"Iniciando Dashboard de Monitoreo Inteligente...")

while True:
    try:
        files = glob.glob(SEARCH_PATTERN)
        
        if not files:
            print("Esperando datos de Spark...")
        else:
            # Ordenar archivos por tiempo de modificación y tomar solo los más recientes
            files_sorted = sorted(files, key=os.path.getmtime, reverse=True)
            # Tomar solo los últimos 20 archivos (aproximadamente los últimos minutos)
            recent_files = files_sorted[:20]
            
            # Leer solo los archivos recientes
            df = pd.concat([pd.read_parquet(f) for f in recent_files], ignore_index=True)
            
            if not df.empty:
                # Convertir end_time a datetime si es string
                if "end_time" in df.columns:
                    df['end_time'] = pd.to_datetime(df['end_time'])
                    
                # Filtrar solo las últimas 10 ventanas (últimos 10 minutos)
                df = df.sort_values(by="end_time", ascending=False).head(10).sort_values(by="end_time", ascending=True)

                # 2. CÁLCULO DE MÉTRICAS REALES (Aquí está la corrección)
                # Uptime = (Pings Totales - Errores) / Pings Totales
                df['uptime_pct'] = ((df['total_pings'] - df['error_count']) / df['total_pings']) * 100
                
                limpiar_pantalla()
                print("=============================================================")
                print("         TABLERO DE CONTROL - CALIDAD DE SERVICIO (QoS)      ")
                print("=============================================================")
                print(f"Ventanas procesadas: {len(df)}")
                
                # Seleccionamos columnas clave para mostrar
                cols_to_show = ['end_time', 'avg_latency', 'total_pings', 'error_count', 'uptime_pct']
                # Redondeamos para que se vea bonito
                print(df[cols_to_show].tail(10).round(2).to_string(index=False))
                
                print("\n---------------------- ESTADO ACTUAL ------------------------")
                
                # --- LÓGICA DE ALERTA ---
                last_row = df.iloc[-1]
                latencia = last_row['avg_latency']
                errores = last_row['error_count']
                uptime = last_row['uptime_pct']

                # Prioridad 1: ¿Está caído? (Uptime bajo o muchos errores)
                if uptime < 100:
                    estado = f"🔴 CAÍDO / INESTABLE (Uptime: {round(uptime, 1)}%)"
                    # Si la latencia es 0 pero hay errores, mostramos N/A en latencia
                    if latencia == 0:
                        latencia_txt = "N/A (Timeout)"
                    else:
                        latencia_txt = f"{round(latencia, 2)} ms"

                # Prioridad 2: ¿Está lento?
                elif latencia > 300:
                    estado = "🟡 LENTO"
                    latencia_txt = f"{round(latencia, 2)} ms"
                
                # Prioridad 3: Todo OK
                else:
                    estado = "🟢 OPERATIVO"
                    latencia_txt = f"{round(latencia, 2)} ms"

                print(f"Estado:   {estado}")
                print(f"Latencia: {latencia_txt}")
                print(f"Errores:  {int(errores)} en el último minuto")
                print("=============================================================")
                print("Presiona Ctrl+C para salir.")
            
    except Exception as e:
        # Ignorar errores de lectura momentáneos por escritura concurrente
        pass

    time.sleep(5)