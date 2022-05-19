import pandas as pd
import numpy as np
import datetime
from datetime import datetime
import locale
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path

repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)

Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']
vacunacion = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto76/vacunacion_t.csv', header=[0, 1], index_col=0)
vacunacion_tot = vacunacion['Total'].copy()
vacunacion_tot.columns.name = 'Fecha'
vacunacion_tot['Esquema_completo'] = vacunacion_tot['Segunda'].shift(14) + vacunacion_tot['Unica'].shift(14).fillna(0)
vacunacion_tot['Esquema_completo_diario'] = vacunacion_tot['Esquema_completo'].diff()
vacunacion_tot['Refuerzo_diario'] = vacunacion_tot['Refuerzo'].diff()
vacunacion_tot['Cuarta_diario'] = vacunacion_tot['Cuarta'].diff()
vacunacion_tot['Esquema_completo_actualizado'] = vacunacion_tot['Esquema_completo_diario'] + vacunacion_tot['Refuerzo_diario'].shift(14).fillna(0) + vacunacion_tot['Cuarta_diario'].shift(14).fillna(0) - vacunacion_tot['Esquema_completo_diario'].shift(168).fillna(0)  - vacunacion_tot['Refuerzo_diario'].shift(168).fillna(0) - vacunacion_tot['Cuarta_diario'].shift(168).fillna(0)
vacunacion_tot = vacunacion_tot.fillna(0)
vacunacion_tot.index = pd.to_datetime(vacunacion_tot.index)
vacunacion_tot.to_csv('test.tsv')
# vacunacion_tot
vacunacion_tot['Esquema_completo_actualizado'].cumsum().plot()
# vacunacion_tot['Esquema_completo'].plot()
piramide_chile_INE = { # INE - Proyección base 2017
    '>=70': 1_614_364,
    '60-69': 1_857_879,
    '50-59': 2_392_614,
    '40-49': 2_658_453,
    '<=39': 11_155_053,
}
fig = go.Figure([
    go.Scatter(
        name='Primer esquema completo',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Esquema_completo_diario'].rolling(7).mean(),
        mode='lines',
        marker=dict(color=Wong[0]),
        showlegend=True
    ),
    go.Scatter(
        name='Primer refuerzo (tercera dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Refuerzo_diario'].rolling(7).mean(),
        mode='lines',
        marker=dict(color=Wong[1]),
        showlegend=True
    ),
    go.Scatter(
        name='Segundo refuerzo (Cuarta dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Cuarta_diario'].rolling(7).mean(),
        marker=dict(color=Wong[2]),
        mode='lines',
        showlegend=True
    )
])
fig.update_layout(
    yaxis_title='Personas diarias',
    title='Vacunacion diaria en Chile (promedio móvil 7 dias)',
    hovermode="x"
)
fig.update_layout(
    template='plotly_white',
    font=dict(
        size=14,
    ),
)
fig.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
fig.update_layout(yaxis_tickformat = ',.0f')
fig.write_html(f'{outputdir}/Vacunacion_diaria_PD76.html')



fig = go.Figure([
    go.Scatter(
        name='Primer esquema completo',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Esquema_completo_diario'].cumsum(),
        mode='lines',
        marker=dict(color=Wong[0]),
        showlegend=True
    ),
    go.Scatter(
        name='Primer refuerzo (tercera dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Refuerzo_diario'].cumsum(),
        mode='lines',
        marker=dict(color=Wong[1]),
        showlegend=True
    ),
    go.Scatter(
        name='Segundo refuerzo (Cuarta dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Cuarta_diario'].cumsum(),
        marker=dict(color=Wong[2]),
        mode='lines',
        showlegend=True
    )
])
fig.update_layout(
    yaxis_title='Personas',
    title='Total de vacunaciones en Chile',
    hovermode="x"
)
fig.update_layout(
    template='plotly_white',
    font=dict(
        size=14,
    ),
)
fig.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
fig.update_layout(yaxis_tickformat = ',.0f')
fig.write_html(f'{outputdir}/Vacunacion_total_PD76.html')


fig = go.Figure([
    go.Scatter(
        name='Primer esquema completo',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Esquema_completo_diario'].cumsum().shift(-30),
        mode='lines',
        marker=dict(color=Wong[0]),
        showlegend=True
    ),
    go.Scatter(
        name='Primer refuerzo (tercera dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Refuerzo_diario'].cumsum().shift(-180),
        mode='lines',
        marker=dict(color=Wong[1]),
        showlegend=True
    ),
    go.Scatter(
        name='Segundo refuerzo (Cuarta dosis)',
        x=vacunacion_tot.index,
        y=vacunacion_tot['Cuarta_diario'].cumsum().shift(-340),
        marker=dict(color=Wong[2]),
        mode='lines',
        showlegend=True
    )
])
fig.update_layout(
    yaxis_title='Personas',
    title='Total de vacunaciones en Chile (desplazada)',
    hovermode="x"
)
fig.update_layout(
    template='plotly_white',
    font=dict(
        size=14,
    ),
)
fig.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
fig.update_layout(yaxis_tickformat = ',.0f')
fig.write_html(f'{outputdir}/Vacunacion_comparacion_PD76.html')
