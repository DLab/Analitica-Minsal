import pandas as pd
import numpy as np
import datetime
import urllib.request
from zipfile import ZipFile
from re import compile
from pathlib import Path
from shutil import rmtree
from datetime import datetime
import locale
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']
repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)

casos = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto5/TotalesNacionales_T.csv', index_col=0)
casos.index = pd.to_datetime(casos.index)
data = casos['Casos nuevos con sintomas'].copy()
# data.iloc[data.argmax()] = data.iloc[data.argmax()-1]/2 + data.iloc[data.argmax()+1]/2
data = data.rolling(7).mean()
data.name = 'Casos'

uci = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto91/Ingresos_UCI_t.csv')
uci.columns = ['Fecha', 'IngresosUCI']
uci['Fecha'] = pd.to_datetime(uci['Fecha'])
uci = uci.set_index('Fecha')

hospital = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto92/Ingresos_Hospital_t.csv')
hospital.columns = ['Fecha', 'IngresosHospital']
hospital['Fecha'] = pd.to_datetime(hospital['Fecha'])
hospital = hospital.set_index('Fecha')

datos = pd.concat([data, hospital, uci], axis=1)

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=datos.index, y=datos['Casos'], name='Casos Síntomaticos', line_color=Wong[0]),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=datos['IngresosHospital'], name='Ingresos a Hospital', line_color=Wong[1]),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=datos['IngresosUCI'], name='Ingresos a UCI', line_color=Wong[2]),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text='Casos Síntomaticos e Ingresos a hospitales y UCI'
)

# Set x-axis title
fig.update_xaxes(title_text='Fecha')

# Set y-axes titles
fig.update_yaxes(title_text="Casoso", secondary_y=False)
fig.update_yaxes(title_text="Ingresos", secondary_y=True)
fig.update_layout(hovermode='x')
fig.update_layout(yaxis1_tickformat = ',.0f')
fig.update_layout(yaxis2_tickformat = ',.0f')

fig.update_layout(template='plotly_white')
fig.update_layout(
    font=dict(
        size=14,
    )
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
fig.update_layout(xaxis_range=['2021-01-01',datos.iloc[-1].name])

# print(fig)

fig.write_html(f'{outputdir}/Casos_ingresos.html')

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=datos.index, y=datos['Casos'], name='Casos Síntomaticos', line_color=Wong[0]),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=(datos['IngresosHospital']/datos['Casos']).rolling(7).mean(), name='Porcentaje de Ingresos a Hospital', line_color=Wong[1]),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=(datos['IngresosUCI']/datos['Casos']).rolling(7).mean(), name='Porcentaje de Ingresos a UCI', line_color=Wong[2]),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text='Casos Síntomaticos y Porcentaje de Ingresos a hospitales y UCI'
)

# Set x-axis title
fig.update_xaxes(title_text='Fecha')

# Set y-axes titles
fig.update_yaxes(title_text="Casoso", secondary_y=False)
fig.update_yaxes(title_text="Porcentaje de ingresos", secondary_y=True)
fig.update_layout(hovermode='x')
fig.update_layout(yaxis1_tickformat = ',.0f')
fig.update_layout(yaxis2_tickformat = '.1%')

fig.update_layout(template='plotly_white')
fig.update_layout(
    font=dict(
        size=14,
    )
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
fig.update_layout(xaxis_range=['2021-01-01',datos.iloc[-1].name])


fig.write_html(f'{outputdir}/Casos_proporcion_ingresos.html')

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
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=vacunacion_tot.index, y=vacunacion_tot['Esquema_completo_actualizado'].cumsum()/sum(piramide_chile_INE.values()), name='Esquema completo actualizado', line_color=Wong[3]),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=datos['IngresosHospital']/datos['Casos'], name='Porcentaje de Ingresos a Hospital', line_color=Wong[1]),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(x=datos.index, y=datos['IngresosUCI']/datos['Casos'], name='Porcentaje de Ingresos a UCI', line_color=Wong[2]),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text='Esquema completo de vacunación y Porcentaje de ingresos a hospitales y UCI'
)

# Set x-axis title
fig.update_xaxes(title_text='Fecha')

# Set y-axes titles
fig.update_yaxes(title_text="Porcentaje de esquema completo", secondary_y=False)
fig.update_yaxes(title_text="Porcentaje de ingresos", secondary_y=True)
fig.update_layout(hovermode='x')
fig.update_layout(yaxis1_tickformat = '.1%')
fig.update_layout(yaxis2_tickformat = '.1%')

fig.update_layout(template='plotly_white')
fig.update_layout(
    font=dict(
        size=14,
    )
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
fig.update_layout(xaxis_range=['2021-01-01',datos.iloc[-1].name])

fig.write_html(f'{outputdir}/Esquema_completo_proporcion_ingresos.html')
