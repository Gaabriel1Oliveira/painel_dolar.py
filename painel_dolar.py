import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from alpha_vantage.timeseries import TimeSeries

# Replace with your Alpha Vantage API Key
API_KEY = "F9FKE00VA27LALAX"  # Get your free API key from Alpha Vantage
ts = TimeSeries(key=API_KEY, output_format='pandas')

st.set_page_config(page_title="Global Dollar Dashboard", layout="wide")
st.title("📈 Global Dollar Pricing Dashboard")

# Asset list and weights
ativos = {
    "USD/MXN": {"ticker": "USDMXN", "peso": 0.10, "function": "FX_DAILY"},
    "USD/BRL": {"ticker": "USDBRL", "peso": 0.10, "function": "FX_DAILY"},
    "USD/AUD": {"ticker": "USDAUD", "peso": 0.10, "function": "FX_DAILY"},
    "USD/ZAR": {"ticker": "USDZAR", "peso": 0.10, "function": "FX_DAILY"},
    "DXY": {"ticker": "DXY", "peso": 0.20, "function": "GLOBAL_QUOTE"},  # DXY might not be directly available
    "Treasury 10Y": {"ticker": "^TNX", "peso": 0.10, "function": "GLOBAL_QUOTE"},  # Need to find alternative
    "VIX": {"ticker": "VIX", "peso": 0.10, "function": "GLOBAL_QUOTE"},  # Need to find alternative
    "Brent": {"ticker": "BRENT", "peso": -0.10, "function": "GLOBAL_QUOTE"},  # Need to find alternative
    "WTI": {"ticker": "WTI", "peso": -0.10, "function": "GLOBAL_QUOTE"},  # Need to find alternative
}


@st.cache_data
def obter_variacao(ticker, function):
    try:
        if function == "FX_DAILY":
            data, meta_data = ts.get_daily(from_symbol=ticker[:3], to_symbol=ticker[3:], outputsize='compact')
            preco_hoje = data['4. close'].iloc[-1]
            preco_ontem = data['4. close'].iloc[-2]
        elif function == "GLOBAL_QUOTE":
            data, meta_data = ts.get_quote(symbol=ticker)
            preco_hoje = float(data['05. price'])
            preco_ontem = float(data['05. price'])  # Approximation - Daily change not directly available
        else:
            return None, None

        variacao = ((preco_hoje - preco_ontem) / preco_ontem) * 100
        return variacao, preco_hoje

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None


# Synthetic index calculation
total_indice = 0
variacoes = {}

st.header("📊 Asset Variations")
col1, col2, col3 = st.columns(3)

for i, (nome, info) in enumerate(ativos.items()):
    variacao, preco = obter_variacao(info['ticker'], info['function'])
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
    try:
        if info['function'] == "FX_DAILY":
            data, meta_data = ts.get_daily(from_symbol=info['ticker'][:3], to_symbol=info['ticker'][3:], outputsize='full')
        elif info['function'] == "GLOBAL_QUOTE":
            data, meta_data = ts.get_quote(symbol=info['ticker'])
            data = pd.DataFrame(data, index=[0])  # Create a DataFrame for consistency
            data['date'] = pd.to_datetime('now')
        else:
            st.warning(f"Chart unavailable for {nome}")
            continue

        if not data.empty:
            if info['function'] == "FX_DAILY":
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=data['4. close'], mode='lines', name=nome))
                fig.update_layout(title=nome, xaxis_title='Date', yaxis_title='Price', height=300)
                st.plotly_chart(fig, use_container_width=True)
            elif info['function'] == "GLOBAL_QUOTE":
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data['date'], y=pd.to_numeric(data['05. price']), mode='lines', name=nome))
                fig.update_layout(title=nome, xaxis_title='Date', yaxis_title='Price', height=300)
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(f"Chart unavailable for {nome}")

    except Exception as e:
        st.warning(f"Error generating chart for {nome}: {e}")