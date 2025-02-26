import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ✅ Configuración de la API desde Streamlit Secrets
API_KEY = st.secrets["API_FOOTBALL_KEY"]
BASE_URL = "https://v3.football.api-sports.io"

# ✅ Inicializar el temporizador dinámico para actualizar cada 60 segundos
st_autorefresh(interval=60000, key="api_timer")  # Se actualiza cada 60 segundos (60000 ms)

# ✅ Calcular el tiempo restante dinámicamente para reinicio de la API
@st.cache_data(ttl=600)  # Se recalcula cada 10 minutos
def get_api_reset_time():
    now = datetime.utcnow()
    reset_hour = (now.hour // 8 + 1) * 8  # Se reinicia cada 8 horas
    reset_time = datetime(now.year, now.month, now.day, reset_hour, 0, 0)
    if reset_time < now:
        reset_time += timedelta(hours=8)
    return reset_time

def get_remaining_time():
    return (get_api_reset_time() - datetime.utcnow()).total_seconds()

# ✅ Función para obtener los partidos del día actual
@st.cache_data(ttl=600)  # Cache de 10 minutos para mejorar rendimiento
def get_matches():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={today}&timezone=UTC"
    headers = {"x-apisports-key": API_KEY}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", [])
    return []

# ✅ Función para obtener cuotas de apuestas
@st.cache_data(ttl=600)
def get_odds():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/odds?date={today}&timezone=UTC"
    headers = {"x-apisports-key": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", [])
    return []

# ✅ Función para analizar y filtrar apuestas por mercados (Incluye EMPATES)
def analyze_odds(odds_data):
    filtered_data = []
    for game in odds_data:
        fixture = game.get("fixture")
        league = game.get("league", {}).get("name", "Desconocida")
        home_team = game.get("teams", {}).get("home", {}).get("name", "Desconocido")
        away_team = game.get("teams", {}).get("away", {}).get("name", "Desconocido")
        timestamp = fixture.get("timestamp", 0)
        match_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")

        for bookmaker in game.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                market_name = bet.get("name", "Desconocido")
                for value in bet.get("values", []):
                    selection = value.get("value", "N/A")
                    odd = value.get("odd", "N/A")

                    # ✅ Filtrar los mercados de interés, incluyendo "Empates"
                    if market_name in ["Match Winner", "Draw No Bet"] or selection == "Draw":
                        filtered_data.append({
                            "Liga": league,
                            "Local": home_team,
                            "Visitante": away_team,
                            "Hora": match_time,
                            "Casa de Apuestas": bookmaker["name"],
                            "Mercado": market_name,
                            "Selección": selection,
                            "Cuota": odd
                        })
    
    return pd.DataFrame(filtered_data)

# ✅ Mostrar partidos y cuotas en la interfaz de Streamlit
def main():
    st.title("BetSmart AIV2 ⚽")
    st.subheader("Sistema de predicción de apuestas deportivas utilizando API-Football")

    # ✅ Mostrar tiempo restante para el reinicio de la API con actualización automática
    st.sidebar.subheader("⏳ Temporizador de Reinicio de API")
    st.sidebar.write(f"Tiempo restante: {timedelta(seconds=int(get_remaining_time()))}")

    # ✅ Botón para actualizar datos manualmente
    if st.button("🔄 Actualizar Datos"):
        with st.spinner("Actualizando información..."):
            matches = get_matches()
            odds = get_odds()
            if matches and odds:
                df_odds = analyze_odds(odds)
                st.success("✅ Datos actualizados correctamente.")

                # ✅ Mostrar tabla con cuotas incluyendo Empates
                st.subheader("📊 Comparación de Cuotas (Incluye Empates)")
                st.dataframe(df_odds)
            else:
                st.error("⚠️ No se encontraron datos para hoy. Inténtalo más tarde.")

    # ✅ Mostrar contador de consultas correctamente
    st.sidebar.subheader("📊 Contador de Consultas a la API")
    total_queries = len(get_matches()) + len(get_odds())
    st.sidebar.write(f"Consultas realizadas: {total_queries}")

    # ✅ Explicación final para los usuarios
    st.markdown("""
    ---
    ### ℹ️ Cómo usar BetSmart AIV2
    1️⃣ Consulta los partidos disponibles y sus cuotas.  
    2️⃣ Filtra los mercados de apuestas y evalúa la rentabilidad.  
    3️⃣ Analiza el valor esperado para encontrar apuestas rentables.  
    4️⃣ Usa el sistema de colores para tomar decisiones informadas.  
    5️⃣ **Apuesta de manera responsable.** 🎯  
    """)

if __name__ == "__main__":
    main()
