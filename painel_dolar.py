import streamlit as st
import pandas as pd
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
            if data is not None and not data.empty:  # Verifica se há dados
                preco_hoje = data['4. close'].iloc[-1]
                preco_ontem = data['4. close'].iloc[-2]
            else:
                return None, None
        elif function == "GLOBAL_QUOTE":
            try:  # Tenta usar GLOBAL_QUOTE, se falhar, retorna None
                data, meta_data = ts.get_quote(symbol=ticker)
                if data is not None and data['05. price'] is not None:  # Verifica se há o preço
                    preco_hoje = float(data['05. price'])
                    preco_ontem = float(data['05. price'])  # Aproximação - Variação diária não diretamente disponível
                else:
                    return None, None
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
            if nome == "DXY":
                variacao_dxy = variacao
            elif nome == "Treasury 10Y":
                variacao_treasury = variacao
            elif nome == "Brent" or nome == "WTI":
                variacao_petroleo = variacao  # Assume Brent e WTI seguem a mesma tendência
        else:
            st.warning(f"Dados indisponíveis para {nome}")

# Análise de cenário
st.markdown("---")
st.header("Análise de Cenário")
sinal_final = analisar_cenario(variacoes.get("USD/BRL", None), variacao_dxy, variacao_treasury, variacao_petroleo)
st.metric("Sinal para Dólar Futuro (BRL)", sinal_final)

# Exibir índice sintético
st.markdown("---")
st.header("Índice Sintético do Dólar")
st.metric("Valor Calculado", f"{total_indice:.2f}", delta=f"{total_indice:.2f}%")
