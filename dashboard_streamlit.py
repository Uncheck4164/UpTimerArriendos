import streamlit as st
import pandas as pd
import glob
import os
import time
import altair as alt

# Configuración de la página
st.set_page_config(
    page_title="Monitor de Uptime",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Dashboard de Monitoreo en Tiempo Real")

# Configuración de rutas
LAKE_DIR = "./datalake/lake2_metrics"
SEARCH_PATTERN = os.path.join(LAKE_DIR, "*.parquet")

def load_data():
    files = glob.glob(SEARCH_PATTERN)
    if not files:
        return pd.DataFrame()
    
    # OPTIMIZACIÓN: Ordenar y leer solo los últimos 50 archivos
    # Esto evita leer todo el historial cada 2 segundos
    files.sort(key=os.path.getmtime)
    recent_files = files[-50:]
    
    data_frames = []
    for f in recent_files:
        try:
            # Verificar que el archivo no esté vacío para evitar ArrowInvalid
            if os.path.getsize(f) > 0:
                data_frames.append(pd.read_parquet(f))
        except Exception:
            continue
            
    if not data_frames:
        return pd.DataFrame()

    df = pd.concat(data_frames, ignore_index=True)
    
    if not df.empty and 'end_time' in df.columns:
        df['end_time'] = pd.to_datetime(df['end_time'])
        df = df.sort_values('end_time')
        
        # Calcular Uptime
        df['uptime_pct'] = ((df['total_pings'] - df['error_count']) / df['total_pings']) * 100
    
    return df

# Contenedor para auto-refresh
placeholder = st.empty()

# Loop de actualización
while True:
    with placeholder.container():
        df = load_data()

        if df.empty:
            st.warning("⏳ Esperando datos en el Data Lake...")
        else:
            # Obtener última métrica
            last_row = df.iloc[-1]
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🕒 Última Actualización", last_row['end_time'].strftime('%H:%M:%S'))
            
            with col2:
                st.metric("📡 Latencia", f"{last_row['avg_latency']:.2f} ms")
            
            with col3:
                st.metric("❌ Errores (1 min)", int(last_row['error_count']))
                
            with col4:
                uptime_val = last_row['uptime_pct']
                st.metric("✅ Uptime", f"{uptime_val:.1f} %", delta=f"{uptime_val - 100:.1f}%" if uptime_val < 100 else "OK")

            # Gráficos
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("Latencia (ms)")
                # Usamos los últimos 60 registros para que el gráfico no se sature
                chart_data = df.tail(60)
                
                chart_latency = alt.Chart(chart_data).mark_line(point=True).encode(
                    x=alt.X('end_time:T', title='Hora'),
                    y=alt.Y('avg_latency:Q', title='ms'),
                    tooltip=['end_time', 'avg_latency']
                ).properties(height=300)
                
                # Línea de umbral
                rule = alt.Chart(pd.DataFrame({'y': [300]})).mark_rule(color='red').encode(y='y')
                
                st.altair_chart(chart_latency + rule, use_container_width=True)

            with col_chart2:
                st.subheader("Uptime (%)")
                chart_uptime = alt.Chart(chart_data).mark_area(
                    line={'color':'darkgreen'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='white', offset=0),
                               alt.GradientStop(color='darkgreen', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X('end_time:T', title='Hora'),
                    y=alt.Y('uptime_pct:Q', scale=alt.Scale(domain=[0, 105]), title='%'),
                    tooltip=['end_time', 'uptime_pct', 'error_count']
                ).properties(height=300)
                st.altair_chart(chart_uptime, use_container_width=True)

            # Tabla de datos recientes
            with st.expander("Ver datos crudos recientes"):
                st.dataframe(df.tail(10).sort_values('end_time', ascending=False))

    # Esperar 2 segundos antes de recargar
    time.sleep(2)
