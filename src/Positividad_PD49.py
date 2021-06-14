import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from pathlib import Path
repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)

dp49 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto49/Positividad_Diaria_Media_T.csv', index_col=0)
fig = go.Figure()
Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']


fig.add_trace(
    go.Scatter(x=dp49.index,
               y=dp49['positividad'],
               mode='lines',
               name='Positividad (DP49)',
               line_color=Wong[0]
              )
)
fig.add_trace(
    go.Scatter(x=dp49.index,
               y=dp49['positividad'].rolling(7).mean(),
               mode='lines',
               name='Media movil 7d de la positividad (DP49)',
               line_color=Wong[1]
              )
)
# fig.add_trace(
#     go.Scatter(x=dp49.index,
#                y=dp49['pcr'],
#                mode='lines',
#                name='PCR (DP49)',
#                line_color=Wong[2],
#                visible='legendonly'
#               )
# )
# fig.add_trace(
#     go.Scatter(x=dp49.index,
#                y=dp49['casos'],
#                mode='lines',
#                name='Casos (DP49)',
#                line_color=Wong[2],
#                visible='legendonly'
#               )
# )

fig.update_layout(hovermode='x')
fig.update_layout(template='plotly_white',
                  title='Positividad PCR nacional (DP49)')
fig.update_layout(yaxis_tickformat = ',.1%')
fig.update_layout(
    font=dict(
        size=14,
    )
)
fig.update_yaxes(rangemode='tozero')
fig.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)

fig.write_html(f'{outputdir}/Positividad_PD49.html')
