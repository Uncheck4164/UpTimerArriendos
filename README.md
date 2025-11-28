# 🚀 UpTimer Arriendos - Sistema de Monitoreo en Tiempo Real

Sistema de monitoreo de uptime y calidad de servicio (QoS) con arquitectura de streaming usando **Apache Kafka** y **Apache Spark**. Monitorea APIs, calcula métricas en tiempo real y visualiza el estado de salud de tus servicios.

![Estado](https://img.shields.io/badge/Estado-Producción-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)

---

## 📋 Requisitos Previos

Antes de empezar, asegúrate de tener instalado:

- **Docker Desktop** (Windows/Mac) o **Docker Engine** (Linux)
- **Docker Compose** v2.0 o superior
- Al menos **4GB de RAM** disponible para Docker
- **Puertos disponibles**: 9092 (Kafka)

---

## 🚀 Inicio Rápido (3 pasos)

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/UpTimerArriendos.git
cd UpTimerArriendos
```

### 2️⃣ Configurar la URL a monitorear (Opcional)

Edita `docker-compose.yml` y cambia la URL de tu API:

```yaml
producer:
  environment:
    - API_URL=http://tu-api.com:8001/health/ # 👈 Cambia esto
```

### 3️⃣ Iniciar todos los servicios

```powershell
# Windows (PowerShell)
docker-compose up -d

# Linux/Mac
docker compose up -d
```

¡Listo! El sistema empezará a monitorear tu API automáticamente.

---

## 📊 Ver el Dashboard en Tiempo Real

Para ver las métricas en vivo:

```powershell
docker-compose logs -f dashboard
```

Verás algo como esto:

```
=============================================================
         TABLERO DE CONTROL - CALIDAD DE SERVICIO (QoS)
=============================================================
Ventanas procesadas: 5
           end_time  avg_latency  total_pings  error_count  uptime_pct
2025-11-28 05:40:00       145.23           60            0       100.0
2025-11-28 05:41:00       152.67           60            0       100.0
2025-11-28 05:42:00       148.91           60            2        96.7
2025-11-28 05:43:00       156.45           60            0       100.0
2025-11-28 05:44:00       162.73           60            0       100.0

---------------------- ESTADO ACTUAL ------------------------
Estado:   🟢 OPERATIVO
Latencia: 162.73 ms
Errores:  0 en el último minuto
=============================================================
```

---

## 🏗️ Arquitectura del Sistema

```
┌──────────────┐        ┌─────────┐        ┌────────────────┐        ┌───────────┐
│   Producer   │──ping──│  Kafka  │──ETL──│  Spark Stream  │──save──│ Datalake  │
│  (Monitor)   │  1/seg │ (Queue) │       │  (Agregación)  │        │ (Parquet) │
└──────────────┘        └─────────┘        └────────────────┘        └───────────┘
                                                                            │
                                                                            │ read
                                                                            ▼
                                                                     ┌───────────┐
                                                                     │ Dashboard │
                                                                     │ (Python)  │
                                                                     └───────────┘
```

### 🔧 Componentes:

| Componente          | Descripción                                                    | Tecnología                                |
| ------------------- | -------------------------------------------------------------- | ----------------------------------------- |
| **Kafka**           | Message broker para ingestar eventos                           | Apache Kafka 3.8 (KRaft)                  |
| **Producer**        | Monitorea tu API cada 1 segundo y envía eventos a Kafka        | Python 3.11 + `requests` + `kafka-python` |
| **Spark Processor** | Procesa streams en tiempo real y agrega métricas cada 1 minuto | Apache Spark 3.5.1 (Structured Streaming) |
| **Datalake**        | Almacena datos crudos y métricas en formato Parquet            | Filesystem compartido                     |
| **Dashboard**       | Visualiza el estado de salud en tiempo real                    | Python 3.11 + `pandas`                    |

### 📂 Estructura del Datalake

```
datalake/
├── lake1_raw/          # Eventos crudos (cada ping individual)
│   ├── part-00000-*.parquet
│   └── _spark_metadata/
├── lake2_metrics/      # Métricas agregadas (ventanas de 1 minuto)
│   ├── part-00000-*.parquet
│   └── _spark_metadata/
└── checkpoints/        # Checkpoints de Spark para tolerancia a fallos
    ├── raw/
    └── metrics/
```

---

## 🛠️ Comandos Útiles

### Ver logs de todos los servicios

```powershell
docker-compose logs -f
```

### Ver logs de un servicio específico

```powershell
docker-compose logs -f producer        # Monitor
docker-compose logs -f spark-processor # Procesador
docker-compose logs -f dashboard       # Dashboard
docker-compose logs -f kafka          # Kafka
```

### Ver estado de los contenedores

```powershell
docker-compose ps
```

### Reiniciar un servicio

```powershell
docker-compose restart producer
docker-compose restart dashboard
```

### Detener todos los servicios

```powershell
docker-compose down
```

### Reconstruir después de cambios en el código

```powershell
docker-compose up -d --build
```

### Limpiar todo (incluye datos)

```powershell
# Detener servicios
docker-compose down

# Limpiar datalake y checkpoints
Remove-Item -Recurse -Force .\datalake\checkpoints\*
Remove-Item -Recurse -Force .\datalake\lake1_raw\*
Remove-Item -Recurse -Force .\datalake\lake2_metrics\*

# Reiniciar
docker-compose up -d
```

---

## ⚙️ Configuración Avanzada

### Cambiar la URL a monitorear

1. Edita `docker-compose.yml`:

```yaml
producer:
  environment:
    - API_URL=http://nueva-url.com:8000/health/
```

2. Reinicia el producer:

```powershell
docker-compose restart producer
```

### Cambiar la frecuencia de monitoreo

Edita `producer.py` y cambia:

```python
time.sleep(1)  # Cambia a 5 para monitorear cada 5 segundos
```

Luego reconstruye:

```powershell
docker-compose up -d --build producer
```

### Cambiar la ventana de agregación

Edita `spark_processor.py`:

```python
.groupBy(
    window(col("timestamp"), "1 minute"),  # Cambia a "5 minutes"
    col("url")
)
```

Reconstruye Spark:

```powershell
docker-compose up -d --build spark-processor
```

---

## 📈 Análisis de Datos

Puedes analizar los datos almacenados con Python/Pandas:

```python
import pandas as pd

# Leer datos crudos (cada ping individual)
df_raw = pd.read_parquet('./datalake/lake1_raw')
print(df_raw.head())

# Leer métricas agregadas (ventanas de 1 minuto)
df_metrics = pd.read_parquet('./datalake/lake2_metrics')
print(df_metrics.describe())

# Calcular uptime total
uptime = ((df_metrics['total_pings'] - df_metrics['error_count']) /
          df_metrics['total_pings'] * 100).mean()
print(f"Uptime promedio: {uptime:.2f}%")
```

---

## 🐛 Solución de Problemas

### ❌ El dashboard muestra siempre el mismo tiempo

**Causa**: Checkpoints antiguos de Spark

**Solución**:

```powershell
# 1. Detener servicios
docker-compose down

# 2. Limpiar checkpoints
Remove-Item -Recurse -Force .\datalake\checkpoints\*
Remove-Item -Recurse -Force .\datalake\lake1_raw\*
Remove-Item -Recurse -Force .\datalake\lake2_metrics\*

# 3. Reiniciar
docker-compose up -d
```

### ❌ El producer no se conecta a Kafka

**Causa**: Kafka tarda en inicializarse

**Solución**: Espera 10-20 segundos. Kafka tiene un healthcheck que espera a que esté listo.

```powershell
# Verificar estado de Kafka
docker-compose logs kafka | Select-String "started"
```

### ❌ No aparecen datos en el dashboard

**Pasos de diagnóstico**:

1. **Verificar que el producer esté enviando datos:**

```powershell
docker-compose logs producer
# Deberías ver: "Enviado: 200 - 150.23ms"
```

2. **Verificar que Spark esté procesando:**

```powershell
docker-compose logs spark-processor
# Deberías ver: "Streaming iniciado..."
```

3. **Esperar al menos 1 minuto** (las ventanas se procesan cada minuto)

4. **Verificar que hay archivos parquet:**

```powershell
Get-ChildItem .\datalake\lake2_metrics\*.parquet
```

### ❌ Error: "no such service: spark"

El servicio se llama `spark-processor`, no `spark`:

```powershell
docker-compose logs spark-processor
```

### ❌ Contenedores se detienen solos

Verifica los logs del contenedor que falló:

```powershell
docker-compose logs --tail=100 [nombre-del-servicio]
```

Revisa recursos de Docker (aumenta RAM si es necesario):

- Docker Desktop → Settings → Resources → Memory: mínimo 4GB

### ❌ Puerto 9092 ya está en uso

Otro proceso está usando el puerto de Kafka.

**Windows**:

```powershell
netstat -ano | findstr :9092
taskkill /PID [PID] /F
```

**Linux/Mac**:

```bash
lsof -ti:9092 | xargs kill -9
```

---

## 📊 Monitoreo de Recursos

Ver uso de CPU/RAM de los contenedores en tiempo real:

```powershell
docker stats
```

Salida esperada:

```
CONTAINER ID   NAME               CPU %     MEM USAGE / LIMIT
c8f1b94d7465   uptimer-dashboard  0.5%      45MiB / 4GiB
55600774d5ac   uptimer-spark      15.2%     850MiB / 4GiB
7d64a5a1a687   uptimer-producer   0.3%      35MiB / 4GiB
8ec2154ace40   kafka              2.1%      450MiB / 4GiB
```

---

## 🔧 Desarrollo y Contribución

### Estructura del Proyecto

```
UpTimerArriendos/
├── producer.py              # Monitor que hace ping a la API
├── spark_processor.py       # Procesamiento de streams con Spark
├── dashboard_reader.py      # Dashboard de visualización
├── requirements.txt         # Dependencias Python
├── docker-compose.yml       # Orquestación de servicios
├── Dockerfile.producer      # Imagen del producer
├── Dockerfile.spark         # Imagen de Spark
├── Dockerfile.dashboard     # Imagen del dashboard
├── datalake/               # Datos generados (no commitear)
│   ├── lake1_raw/
│   ├── lake2_metrics/
│   └── checkpoints/
└── README.md               # Este archivo
```

### Modificar el código

1. Edita el archivo Python correspondiente
2. Reconstruye la imagen:

```powershell
docker-compose up -d --build [servicio]
```

Ejemplos:

```powershell
docker-compose up -d --build producer
docker-compose up -d --build spark-processor
docker-compose up -d --build dashboard
```

### Ejecutar comandos dentro de un contenedor

```powershell
# Acceder al shell de Spark
docker exec -it uptimer-spark bash

# Acceder al shell del producer
docker exec -it uptimer-producer bash

# Ver archivos del datalake
docker exec -it uptimer-dashboard ls -lh /app/datalake/lake2_metrics/
```

---

## 📝 Notas Técnicas

- **Checkpoints**: Spark guarda checkpoints en `./datalake/checkpoints/` para tolerancia a fallos
- **Watermark**: Configurado a 1 minuto para manejar eventos tardíos
- **Ventanas**: Agregación de 1 minuto (tumbling window)
- **Formato**: Parquet con compresión Snappy
- **Persistencia**: Los datos sobreviven reinicios gracias al volumen compartido
- **Dashboard**: Se actualiza cada 5 segundos leyendo los últimos 20 archivos parquet

---

## 📚 Tecnologías Utilizadas

- **[Apache Kafka 3.8](https://kafka.apache.org/)** - Message Broker con KRaft (sin Zookeeper)
- **[Apache Spark 3.5.1](https://spark.apache.org/)** - Structured Streaming
- **[Python 3.11](https://www.python.org/)** - Lenguaje principal
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestación de contenedores
- **[Pandas](https://pandas.pydata.org/)** - Análisis de datos
- **[Parquet](https://parquet.apache.org/)** - Formato columnar eficiente

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🆘 Soporte

Si tienes problemas:

1. Revisa la sección **🐛 Solución de Problemas**
2. Verifica los logs: `docker-compose logs -f`
3. Abre un issue en GitHub con:
   - Logs completos del error
   - Sistema operativo
   - Versión de Docker

---

## 📞 Contacto

**Autor**: Tu Nombre  
**Email**: tu-email@ejemplo.com  
**GitHub**: [@tu-usuario](https://github.com/tu-usuario)

---

⭐ Si este proyecto te fue útil, dale una estrella en GitHub!
