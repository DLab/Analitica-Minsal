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
casos['Casos nuevos totales + antigeno + probables'] = dp5[['Casos nuevos totales', 'Casos nuevos confirmados por antigeno', 'Casos nuevos probables']].sum(axis=1)
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
               y=casos['Casos nuevos totales + antigeno + probables'],
               mode='lines',
               name='Casos nuevos totales + antigeno + probables (DP5)',
               line_color=Wong[1]
              )
)
fig.update_layout(hovermode='x')
fig.update_layout(template='plotly_white',
                  title='Comparación de los casos nuevos totales con los casos probables y casos positivos por test de antígeno')
fig.update_layout(yaxis_tickformat = ',')
fig.write_html(f'{outputdir}/Casos_Nuevos_Mas_Probables.html')
