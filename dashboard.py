def criar_heatmap(df_metricas):
    """Cria um gráfico de barras horizontal colorido das ações"""
    # Ordenar por distância percentual (da maior para a menor)
    df_sorted = df_metricas.sort_values('Distancia_Pct', ascending=True)
    
    # Criar coluna de cor baseada na distância
    cores = []
    for val in df_sorted['Distancia_Pct']:
        if val > 10:
            cores.append('darkgreen')
        elif val > 0:
            cores.append('lightgreen')
        elif val > -10:
            cores.append('lightcoral')
        else:
            cores.append('darkred')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df_sorted['Ticker'],
        x=df_sorted['Distancia_Pct'],
        orientation='h',
        marker_color=cores,
        text=[f"{v:.1f}%" for v in df_sorted['Distancia_Pct']],
        textposition='outside',
        textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{y}</b><br>Distância da MM200: %{x:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Distância das Ações em Relação à MM200 (%)',
        xaxis_title='Distância Percentual (%)',
        yaxis_title='',
        height=max(600, len(df_sorted) * 25),  # Altura dinâmica baseada no número de ações
        margin=dict(l=100, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='white',
            zerolinewidth=2
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.05)'
        )
    )
    
    # Adicionar linha vertical no zero
    fig.add_vline(x=0, line_dash="dash", line_color="yellow", line_width=2)
    
    return fig
