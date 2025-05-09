import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from alpha_vantage.timeseries import TimeSeries

# Substitua com sua chave da API Alpha Vantage
API_KEY = "F9FKE00VA27LALAX"  # Obtenha sua chave de API gratuita do Alpha Vantage
ts = TimeSeries(key=API_KEY, output_format='pandas')

st.set_page_config(page_title="Painel de Preços do Dólar Global", layout="wide")
st.title("Painel de Preços do Dólar Global")

# Lista de ativos e pesos
ativos = {
    "USD/MXN": {"ticker": "USDMXN", "peso": 0.10, "function": "FX_DAILY"},
    "USD/BRL": {"ticker": "USDBRL", "peso": 0.10, "function": "FX_DAILY"},
    "USD/AUD": {"ticker": "USDAUD", "peso": 0.10, "function": "FX_DAILY"},
    "USD/ZAR": {"ticker": "USDZAR", "peso": 0.10, "function": "FX_DAILY"},
    "DXY": {"ticker": "DXY", "peso": 0.20, "function": "GLOBAL_QUOTE"},  # DXY pode não estar diretamente disponível
    "Treasury 10Y": {"ticker": "^TNX", "peso": 0.10, "function": "GLOBAL_QUOTE"},  # Precisa encontrar alternativa
    "VIX": {"ticker": "VIX", "peso": 0.10, "function": "GLOBAL_QUOTE"},  # Precisa encontrar alternativa
    "Brent": {"ticker": "BRENT", "peso": -0.10, "function": "GLOBAL_QUOTE"},  # Precisa encontrar alternativa
    "WTI": {"ticker": "WTI", "peso": -0.10, "function": "GLOBAL_QUOTE"},  # Precisa encontrar alternativa
}


@st.cache_data
def obter_variacao(ticker, function):
    try:
        if function == "FX_DAILY":
            data, meta_data = ts.get_daily(symbol=ticker[:3] + ticker[3:], outputsize='compact')
            preco_hoje = data['4. close'].iloc[-1]
            preco_ontem = data['4. close'].iloc[-2]
        elif function == "GLOBAL_QUOTE":
            try:  # Tenta usar GLOBAL_QUOTE, se falhar, retorna None
                data, meta_data = ts.get_quote(symbol=ticker)
                preco_hoje = float(data['05. price'])
                preco_ontem = float(data['05. price'])  # Aproximação - Variação diária não diretamente disponível
            except Exception as e:
                print(f"Erro ao obter GLOBAL_QUOTE para {ticker}: {e}")
                return None, None
        else:
            return None, None

        variacao = ((preco_hoje - preco_ontem) / preco_ontem) * 100
        return variacao, preco_hoje

    except Exception as e:
        print(f"Erro ao buscar dados para {ticker}: {e}")
        return None, None


# Cálculo do índice sintético
total_indice = 0
variacoes = {}

st.header("Variações de Ativos")
col1, col2, col3 = st.columns(3)

for i, (nome, info) in enumerate(ativos.items()):
    variacao, preco = obter_variacao(info['ticker'], info['function'])
    if variacao is not None and preco is not None:
        variacoes[nome] = variacao
        total_indice += variacao * info['peso']
        with [col1, col2, col3][i % 3]:
            try:
                sinal = "Compra" if variacao > 0 else "Venda"
                st.metric(label=nome, value=f"{preco:.4f}", delta=f"{variacao:.2f}% ({sinal})")
            except Exception as e:
                st.warning(f"Erro ao exibir métrica para {nome}: {e}")
    else:
        with [col1, col2, col3][i % 3]:
            st.warning(f"Dados indisponíveis para {nome}")

# Exibir índice sintético
st.markdown("---")
st.header("Índice Sintético do Dólar")
st.metric("Valor Calculado", f"{total_indice:.2f}", delta=f"{total_indice:.2f}%")
