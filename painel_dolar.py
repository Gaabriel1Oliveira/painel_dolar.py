
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Global Dollar Dashboard", layout="wide")
st.title("📈 Global Dollar Pricing Dashboard")

# Asset list and weights
ativos = {
    "USD/MXN": {"ticker": "USDMXN=X", "peso": 0.10},
    "USD/BRL": {"ticker": "USDBRL=X", "peso": 0.10},
    "USD/AUD": {"ticker": "USDAUD=X", "peso": 0.10},
    "USD/ZAR": {"ticker": "USDZAR=X", "peso": 0.10},
    "DXY": {"ticker": "DX-Y.NYB", "peso": 0.20},
    "Treasury 10Y": {"ticker": "^TNX", "peso": 0.10},
    "VIX": {"ticker": "^VIX", "peso": 0.10},
    "Brent": {"ticker": "BZ=F", "peso": -0.10},
    "WTI": {"ticker": "CL=F", "peso": -0.10},
}

# Function to get percentage change
@st.cache_data
def obter_variacao(ticker):
    dados = yf.download(ticker, period='2d', interval='1d', progress=False)
    if len(dados) >= 2:
        preco_ontem = dados['Close'].iloc[0]
        preco_hoje = dados['Close'].iloc[1]
        variacao = ((preco_hoje - preco_ontem) / preco_ontem) * 100
        return variacao, preco_hoje
    else:
        return None, None

# Synthetic index calculation
total_indice = 0
variacoes = {}

st.header("📊 Asset Variations")
col1, col2, col3 = st.columns(3)

for i, (nome, info) in enumerate(ativos.items()):
    variacao, preco = obter_variacao(info['ticker'])
    if variacao is not None and preco is not None:
        variacoes[nome] = variacao
        total_indice += variacao * info['peso']
        with [col1, col2, col3][i % 3]:
            try:
                st.metric(label=nome, value=f"{preco:.4f}", delta=f"{variacao:.2f}%")
            except Exception as e:
                st.warning(f"Error displaying metric for {nome}: {e}")
    else:
        with [col1, col2, col3][i % 3]:
            st.warning(f"Data unavailable for {nome}")

# Display synthetic index
st.markdown("---")
st.header("🧮 Synthetic Dollar Index")
st.metric("Calculated Value", f"{total_indice:.2f}", delta=f"{total_indice:.2f}%")

# Graphics
st.markdown("---")
st.header("📉 Asset Charts")

for nome, info in ativos.items():
    dados = yf.download(info['ticker'], period='7d', interval='1h', progress=False)
    if not dados.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dados.index, y=dados['Close'], mode='lines', name=nome))
        fig.update_layout(title=nome, xaxis_title='Date', yaxis_title='Price', height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"Chart unavailable for {nome}")