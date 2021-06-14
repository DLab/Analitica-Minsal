import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from pathlib import Path
repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)
dp5 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto5/TotalesNacionales_T.csv', index_col=0)
dp5['Casos nuevos probables'] = dp5['Casos probables acumulados'].diff()
casos = dp5[['Casos nuevos totales']].copy()
casos['Casos nuevos totales + probables'] = dp5[['Casos nuevos totales', 'Casos nuevos probables']].sum(axis=1)
fig = go.Figure()
Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']
fig.add_trace(
    go.Scatter(x=casos.index,
               y=casos['Casos nuevos totales'],
               mode='lines',
               name='Casos nuevos totales (DP5)',
               line_color=Wong[0]
              )
)
fig.add_trace(
    go.Scatter(x=casos.index,
               y=casos['Casos nuevos totales + probables'],
               mode='lines',
               name='Casos nuevos totales + probables (DP5)',
               line_color=Wong[1]
              )
)
fig.add_trace(
    go.Scatter(x=dp5.index,
               y=dp5['Casos nuevos probables'],
               mode='lines',
               name='Diferencia',
               line_color=Wong[2],
               visible='legendonly'
              )
)
fig.update_layout(hovermode='x')
fig.update_layout(template='plotly_white',
                  title='Comparación de los casos nuevos totales con los casos probables')
fig.update_layout(yaxis_tickformat = ',')


fig.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)

fig.write_html(f'{outputdir}/Casos_Nuevos_Mas_Probables.html')
