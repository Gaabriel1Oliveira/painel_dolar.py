import streamlit as st
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import yfinance as yf
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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
    "DXY": {"ticker": "DXY", "peso": 0.20, "function": "GLOBAL_QUOTE"},
    "Treasury 10Y": {"ticker": "^TNX", "peso": 0.10, "function": "GLOBAL_QUOTE"},
    "VIX": {"ticker": "VIX", "peso": 0.10, "function": "GLOBAL_QUOTE"},
    "Brent": {"ticker": "BRENT", "peso": -0.10, "function": "GLOBAL_QUOTE"},
    "WTI": {"ticker": "WTI", "peso": -0.10, "function": "GLOBAL_QUOTE"},
}


@st.cache_data
def obter_variacao(ticker, function):
    try:
        preco_hoje = None
        preco_ontem = None

        if function == "FX_DAILY":
            data = ts.get_daily(symbol=ticker[:3] + ticker[3:], outputsize='compact')[0]
            if data is not None and not data.empty:
                preco_hoje = data['4. close'].iloc[-1]
                preco_ontem = data['4. close'].iloc[-2]
            else:
                logging.warning(f"Dados ausentes da Alpha Vantage para {ticker}")
                return None, None

        elif function == "GLOBAL_QUOTE":
            if ticker == "DXY":
                ticker_yf = "DX-Y.NYB"  # Ticker correto para DXY no Yahoo Finance
            elif ticker == "^TNX":
                ticker_yf = "^TNX"  # Ticker correto para Treasury 10Y
            elif ticker == "VIX":
                ticker_yf = "^VIX"  # Ticker correto para VIX
            elif ticker == "BRENT":
                ticker_yf = "BZ=F"  # Ticker correto para Brent
            elif ticker == "WTI":
                ticker_yf = "CL=F"  # Ticker correto para WTI
            else:
                logging.warning(f"Ticker {ticker} não suportado para GLOBAL_QUOTE")
                return None, None

            data_yf = yf.download(ticker_yf, period="2d", interval="1d")
            if data_yf is not None and not data_yf.empty:
                preco_hoje = data_yf['Close'].iloc[-1]
                preco_ontem = data_yf['Close'].iloc[-2]
            else:
                logging.warning(f"Dados ausentes do Yahoo Finance para {ticker}")
                return None, None

        else:
            logging.error(f"Função desconhecida para {ticker}: {function}")
            return None, None

        if preco_hoje is not None and preco_ontem is not None:
            variacao = ((preco_hoje - preco_ontem) / preco_ontem) * 100
            return variacao, preco_hoje
        else:
            return None, None

    except Exception as e:
        logging.error(f"Erro ao obter dados para {ticker}: {e}")
        return None, None


def analisar_cenario(variacao_brl, variacao_dxy, variacao_treasury, variacao_petroleo):
    sinal = "Neutro"
    if variacao_dxy is not None and variacao_brl is not None:
        if variacao_dxy > 0 and variacao_brl > 0:
            sinal = "Compra (Dólar forte globalmente)"
        elif variacao_dxy < 0 and variacao_brl < 0:
            sinal = "Venda (Dólar fraco globalmente)"
    if variacao_treasury is not None and variacao_brl is not None:
        if variacao_treasury > 0 and variacao_brl > 0:
            sinal = "Compra (Aumento dos juros nos EUA)"
        elif variacao_treasury < 0 and variacao_brl < 0:
            sinal = "Venda (Queda dos juros nos EUA)"
    if variacao_petroleo is not None and variacao_brl is not None:
        if variacao_petroleo < 0 and variacao_brl > 0:
            sinal = "Compra (Petróleo em queda, pressão sobre o real)"
        elif variacao_petroleo > 0 and variacao_brl < 0:
            sinal = "Venda (Petróleo em alta, suporte ao real)"
    return sinal


# Cálculo do índice sintético
total_indice = 0
variacoes = {}

st.header("Variações de Ativos")
col1, col2, col3 = st.columns(3)

variacao_dxy = None
variacao_treasury = None
variacao_petroleo = None

for i, (nome, info) in enumerate(ativos.items()):
    variacao, preco = obter_variacao(info['ticker'], info['function'])
    with [col1, col2, col3][i % 3]:  # Coloca o with fora do if para sempre exibir algo
        if variacao is not None and preco is not None:
            variacoes[nome] = variacao
            total_indice += variacao * info['peso']
            try:
                sinal = "Compra" if variacao > 0 else "Venda"
                st.metric(label=nome, value=f"{preco:.4f}", delta=f"{variacao:.2f}% ({sinal})")
            except Exception as e:
                st.warning(f"Erro ao exibir métrica para {nome}: {e}")
        else:
            st.warning(f"Dados indisponíveis para {nome}")
        if nome == "DXY" and variacao is not None:
            variacao_dxy = variacao
        elif nome == "Treasury 10Y" and variacao is not None:
            variacao_treasury = variacao
        elif (nome == "Brent" or nome == "WTI") and variacao is not None:
            variacao_petroleo = variacao  # Assume Brent e WTI seguem a mesma tendência

# Análise de cenário
st.markdown("---")
st.header("Análise de Cenário")
sinal_final = analisar_cenario(variacoes.get("USD/BRL", None), variacao_dxy, variacao_treasury, variacao_petroleo)
st.metric("Sinal para Dólar Futuro (BRL)", sinal_final)

# Exibir índice sintético
st.markdown("---")
st.header("Índice Sintético do Dólar")
st.metric("Valor Calculado", f"{total_indice:.2f}", delta=f"{total_indice:.2f}%")
