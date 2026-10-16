import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Dashboard Ibovespa - Análise de Amplitude",
    page_icon="📊",
    layout="wide"
)

# Lista das principais ações do Ibovespa
IBOV_TICKERS = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA',
    'ABEV3.SA', 'B3SA3.SA', 'JBSS3.SA', 'WEGE3.SA', 'RENT3.SA',
    'SUZB3.SA', 'MGLU3.SA', 'LREN3.SA', 'VIVT3.SA', 'GGBR4.SA',
    'CSNA3.SA', 'USIM5.SA', 'RAIL3.SA', 'EMBR3.SA', 'BRFS3.SA',
    'BRML3.SA', 'BRDT3.SA', 'PETR3.SA', 'PRIO3.SA', 'CSAN3.SA',
    'ELET3.SA', 'ELET6.SA', 'TAEE11.SA', 'TRPL4.SA', 'CPFE3.SA',
    'EQTL3.SA', 'ENGI11.SA', 'SBSP3.SA', 'SANB11.SA', 'ITSA4.SA',
    'BPAC11.SA', 'BPAN4.SA', 'BBSE3.SA', 'BBDC3.SA', 'BRSR6.SA',
    'ABCB4.SA', 'BIDI11.SA', 'CRFB3.SA', 'PCAR3.SA', 'AMER3.SA',
    'LWSA3.SA', 'ALSO3.SA', 'MULT3.SA', 'VVAR3.SA', 'CEAB3.SA',
    'RADL3.SA', 'FLRY3.SA', 'HAPV3.SA', 'TOTS3.SA', 'POSI3.SA',
    'BASA3.SA', 'BRAP4.SA', 'FESA4.SA', 'GOAU4.SA', 'METR3.SA',
    'LEVE3.SA', 'WHRL4.SA', 'CYRE3.SA', 'MRVE3.SA', 'EZTC3.SA',
    'TEND3.SA', 'DIRR3.SA', 'YDUQ3.SA', 'COGN3.SA', 'CVCB3.SA',
    'SMTO3.SA', 'SLCE3.SA', 'HYPE3.SA', 'ODPV3.SA'
]

@st.cache_data(ttl=3600)
def carregar_dados_ibovespa():
    """Baixa dados históricos de todas as ações do Ibovespa"""
    st.info("🔄 Carregando dados do Yahoo Finance... Isso pode levar 1-2 minutos.")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)
    
    dados_completos = {}
    tickers_validos = []
    
    progress_bar = st.progress(0)
    total_tickers = len(IBOV_TICKERS)
    
    for i, ticker in enumerate(IBOV_TICKERS):
        try:
            # Download dos dados
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            # Verificar se o DataFrame não está vazio
            if df is None or len(df) == 0:
                continue
            
            # CORREÇÃO: yfinance novo retorna MultiIndex nas colunas
            # Precisamos "achatar" o DataFrame
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Garantir que temos pelo menos 200 dias de dados
            if len(df) >= 200:
                dados_completos[ticker] = df
                tickers_validos.append(ticker)
        except Exception as e:
            continue
        
        progress_bar.progress((i + 1) / total_tickers)
    
    st.success(f"✅ {len(tickers_validos)} ações carregadas com sucesso!")
    return dados_completos, tickers_validos

def calcular_metricas(dados_completos, tickers_validos):
    """Calcula MM200 e métricas de amplitude"""
    resultados = []
    
    for ticker in tickers_validos:
        df = dados_completos[ticker]
        
        # CORREÇÃO: Extrair valores escalares corretamente
        close_series = df['Close']
        
        # Último preço (garantir que é um número simples)
        preco_atual = float(close_series.iloc[-1])
        
        # Calcular MM200
        mm200_serie = close_series.rolling(window=200).mean()
        mm200 = float(mm200_serie.iloc[-1])
        
        # Calcular distância percentual
        distancia_pct = ((preco_atual - mm200) / mm200) * 100
        
        # Distância de ontem para calcular tendência
        if len(df) > 1:
            preco_ontem = float(close_series.iloc[-2])
            mm200_ontem = float(mm200_serie.iloc[-2])
            distancia_ontem = ((preco_ontem - mm200_ontem) / mm200_ontem) * 100
            variacao_distancia = distancia_pct - distancia_ontem
        else:
            variacao_distancia = 0.0
        
        # CORREÇÃO: Converter para bool Python nativo (não Series)
        acima_mm = bool(preco_atual > mm200)
        
        resultados.append({
            'Ticker': ticker.replace('.SA', ''),
            'Preco': preco_atual,
            'MM200': mm200,
            'Distancia_Pct': distancia_pct,
            'Acima_MM': acima_mm,
            'Variacao_Distancia': variacao_distancia
        })
    
    return pd.DataFrame(resultados)

def determinar_cenario(df_metricas):
    """Determina o cenário atual do mercado"""
    total_acoes = len(df_metricas)
    
    # CORREÇÃO: Usar .sum() direto na coluna booleana
    acima_mm = int(df_metricas['Acima_MM'].sum())
    pct_acima = (acima_mm / total_acoes) * 100
    
    # Filtrar ações acima e abaixo da MM200
    # CORREÇÃO: Usar máscara booleana corretamente
    acoes_acima = df_metricas[df_metricas['Acima_MM'] == True]
    acoes_abaixo = df_metricas[df_metricas['Acima_MM'] == False]
    
    distancia_media_acima = float(acoes_acima['Distancia_Pct'].mean()) if len(acoes_acima) > 0 else 0
    distancia_media_abaixo = float(acoes_abaixo['Distancia_Pct'].mean()) if len(acoes_abaixo) > 0 else 0
    
    # Variação média da distância
    variacao_media = float(df_metricas['Variacao_Distancia'].mean())
    
    # Lógica dos 4 cenários
    if pct_acima > 60:  # Maioria acima da MM200
        if variacao_media > 0:
            cenario = "🟢 ALTA FORTE"
            descricao = "Compradores dominando - Mercado em tendência de alta saudável"
            cor = "green"
        else:
            cenario = "🟡 ALTA CANSADA"
            descricao = "Perda de força compradora - Aguardar oportunidade"
            cor = "orange"
    else:  # Maioria abaixo da MM200
        if variacao_media < 0:
            cenario = "🔴 BAIXA FORTE"
            descricao = "Vendedores dominando - Mercado em tendência de baixa"
            cor = "red"
        else:
            cenario = "🟠 BAIXA CANSADA"
            descricao = "Perda de força vendedora - Possível reversão"
            cor = "darkorange"
    
    return {
        'cenario': cenario,
        'descricao': descricao,
        'cor': cor,
        'pct_acima': pct_acima,
        'distancia_media_acima': distancia_media_acima,
        'distancia_media_abaixo': distancia_media_abaixo,
        'variacao_media': variacao_media,
        'total_acoes': total_acoes,
        'acima_mm': acima_mm
    }

def criar_medidor(pct_acima, cenario, cor):
    """Cria um medidor visual do cenário"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_acima,
        title={'text': f"% de Ações Acima da MM200<br><span style='font-size:0.8em;color:gray'>{cenario}</span>"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': cor},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 60], 'color': "lightyellow"},
                {'range': [60, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': pct_acima
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def criar_heatmap(df_metricas):
    """Cria um heatmap das ações"""
    fig = px.treemap(
        df_metricas,
        path=[px.Constant("Ibovespa"), 'Ticker'],
        values='Distancia_Pct',
        color='Distancia_Pct',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        title='Heatmap de Distância das Ações em Relação à MM200 (%)'
    )
    fig.update_layout(height=500)
    return fig

def criar_scatter(df_metricas):
    """Cria gráfico de dispersão"""
    # CORREÇÃO: Criar coluna com valor absoluto para o tamanho
    df_plot = df_metricas.copy()
    df_plot['Tamanho'] = df_plot['Distancia_Pct'].abs()
    
    fig = px.scatter(
        df_plot,
        x='MM200',
        y='Preco',
        size='Tamanho',  # Usa valor absoluto (sempre positivo)
        color='Distancia_Pct',  # Cor indica se está acima (verde) ou abaixo (vermelho)
        hover_name='Ticker',
        color_continuous_scale='RdYlGn',
        title='Distribuição: Preço vs MM200',
        labels={'MM200': 'Média Móvel 200', 'Preco': 'Preço Atual'}
    )
    
    max_val = max(df_plot['MM200'].max(), df_plot['Preco'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Preço = MM200'
    ))
    
    fig.update_layout(height=500)
    return fig

# ==================== MAIN ====================

st.title("📊 Dashboard Ibovespa - Análise de Amplitude de Mercado")
st.markdown("---")

# Carregar dados
dados_completos, tickers_validos = carregar_dados_ibovespa()

if len(tickers_validos) == 0:
    st.error("❌ Não foi possível carregar os dados. Verifique sua conexão com a internet.")
    st.stop()

# Calcular métricas
df_metricas = calcular_metricas(dados_completos, tickers_validos)

# Determinar cenário
cenario_info = determinar_cenario(df_metricas)

# ==================== EXIBIÇÃO ====================

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader(cenario_info['cenario'])
    st.write(cenario_info['descricao'])
    
with col2:
    st.metric(
        "Ações Acima da MM200",
        f"{cenario_info['acima_mm']}/{cenario_info['total_acoes']}",
        f"{cenario_info['pct_acima']:.1f}%"
    )

with col3:
    st.metric(
        "Variação Média da Distância",
        f"{cenario_info['variacao_media']:.2f}%",
        "Aumentando" if cenario_info['variacao_media'] > 0 else "Diminuindo"
    )

st.markdown("---")

st.plotly_chart(criar_medidor(cenario_info['pct_acima'], cenario_info['cenario'], cenario_info['cor']), use_container_width=True)

st.markdown("---")

tab1, tab2, tab3 = st.tabs([" Heatmap de Ações", "📊 Distribuição (Scatter)", "📋 Tabela Detalhada"])

with tab1:
    st.plotly_chart(criar_heatmap(df_metricas), use_container_width=True)

with tab2:
    st.plotly_chart(criar_scatter(df_metricas), use_container_width=True)

with tab3:
    df_sorted = df_metricas.sort_values('Distancia_Pct', ascending=False)
    
    df_display = df_sorted.copy()
    df_display['Preco'] = df_display['Preco'].round(2)
    df_display['MM200'] = df_display['MM200'].round(2)
    df_display['Distancia_Pct'] = df_display['Distancia_Pct'].round(2)
    df_display['Status'] = df_display['Acima_MM'].apply(lambda x: '✅ Acima' if x else '❌ Abaixo')
    
    st.dataframe(
        df_display[['Ticker', 'Preco', 'MM200', 'Distancia_Pct', 'Status']],
        use_container_width=True,
        height=600
    )

st.markdown("---")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Dados: Yahoo Finance | Total de ações analisadas: {len(tickers_validos)}")

if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
