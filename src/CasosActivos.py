import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from pathlib import Path
repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)

casos = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto3/TotalesPorRegion_std.csv')
casos['Fecha'] = pd.to_datetime(casos['Fecha'])
casos_sintomaticos = casos[casos['Categoria']=='Casos nuevos con sintomas'].pivot(index='Fecha', columns='Region', values='Total')
casos_nuevos = casos[casos['Categoria']=='Casos nuevos totales'].pivot(index='Fecha', columns='Region', values='Total')
casos_activos_conf = casos[casos['Categoria']=='Casos activos confirmados'].pivot(index='Fecha', columns='Region', values='Total')
casos_activos_prob = casos[casos['Categoria']=='Casos activos probables'].pivot(index='Fecha', columns='Region', values='Total')
casos_nuevos_prob = casos[casos['Categoria']=='Casos probables acumulados'].pivot(index='Fecha', columns='Region', values='Total').diff()
casos_nuevos_antigeno = casos[casos['Categoria']=='Casos nuevos confirmados por antigeno'].pivot(index='Fecha', columns='Region', values='Total')
casos_sintomaticos.rename(columns={'Total': 'Chile'}, inplace=True)
casos_nuevos.rename(columns={'Total': 'Chile'}, inplace=True)
casos_activos_conf.rename(columns={'Total': 'Chile'}, inplace=True)
casos_activos_prob.rename(columns={'Total': 'Chile'}, inplace=True)
casos_nuevos_prob.rename(columns={'Total': 'Chile'}, inplace=True)
casos_nuevos_antigeno.rename(columns={'Total': 'Chile'}, inplace=True)
casos_nuevos_prob_antigeno = casos_nuevos.add(casos_nuevos_prob, fill_value=0)
casos_nuevos_prob_antigeno = casos_nuevos_prob_antigeno.add(casos_nuevos_antigeno, fill_value=0)
datos_regiones = pd.read_csv('https://raw.githubusercontent.com/ivanMSC/COVID19_Chile/master/utils/regionesChile.csv')
casos_activos = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto46/activos_vs_recuperados.csv')
casos_activos.rename(columns={
    'fecha_primeros_sintomas': 'Fecha',
    'activos': 'Activos',
    'recuperados': 'Recuperados'
}, inplace=True)
casos_activos['Fecha'] = pd.to_datetime(casos_activos['Fecha'])
casos_activos['Activos'] = pd.to_numeric(casos_activos['Activos'])
casos_activos['Recuperados'] = pd.to_numeric(casos_activos['Recuperados'])
casos_activos.set_index('Fecha', inplace=True)
casos_uci = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto8/UCI_T.csv')
casos_uci.rename(columns={'Region': 'Fecha'}, inplace=True)
datos_regiones = pd.merge(datos_regiones, casos_uci.iloc[[0,1]].T, left_on='numTradicional', right_on=0)
datos_regiones.drop(columns=0, inplace=True)
datos_regiones.rename(columns={1: 'Poblacion'}, inplace=True)
casos_uci = casos_uci.iloc[2:]
casos_uci['Fecha'] = pd.to_datetime(casos_uci['Fecha'])
casos_uci.set_index('Fecha', inplace=True)
casos_uci['Chile'] = casos_uci[list(casos_uci.columns)].sum(axis=1)
DP19 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto19/CasosActivosPorComuna_std.csv')
activos_dp19 = DP19[DP19['Comuna']=='Total'].pivot(index='Fecha', columns='Codigo region', values='Casos activos').sum(axis=1)
activos_dp19.index = pd.to_datetime(activos_dp19.index)
activos_dp19
DP5 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto5/TotalesNacionales_T.csv')
DP5['Fecha'] = pd.to_datetime(DP5['Fecha'])
DP5 = DP5.set_index('Fecha')

fig = go.Figure()
Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']


fig.add_trace(
    go.Scatter(x=casos_activos.index,
               y=casos_activos['Activos'],
               mode='lines',
               name='Activos (DP46)',
               line_color=Wong[0]
              )
)
fig.add_trace(
    go.Scatter(x=casos_nuevos.index,
               y=casos_nuevos['Chile'].rolling(11).sum(),
               mode='lines',
               name='Inferencia de activos (DP3)',
               line_color=Wong[1]
              )
)
fig.add_trace(
    go.Scatter(x=casos_nuevos.index,
               y=casos_nuevos['Chile'].rolling(11).sum().shift(-6),
               mode='lines',
               name='Inferencia de activos (DP3) (shift-6)',
               line_color=Wong[5],
               visible='legendonly',
              )
)
fig.add_trace(
    go.Scatter(x=casos_nuevos_prob_antigeno.index,
               y=casos_nuevos_prob_antigeno['Chile'].rolling(11).sum(),
               mode='lines',
               name='Inferencia de activos (PCR + Probables + Antígeno) (DP3)',
               line_color=Wong[6],
               visible='legendonly',
              )
)
fig.add_trace(
    go.Scatter(x=activos_dp19.index,
               y=activos_dp19,
               mode='lines',
               name='Activos (DP19)',
               line_color=Wong[2]
              )
)
fig.add_trace(
    go.Scatter(x=DP5.index,
               y=DP5['Casos activos por FD'],
               mode='lines',
               name='Casos Activos FD (DP5)',
               line_color=Wong[3]
              )
)
fig.add_trace(
    go.Scatter(x=DP5.index,
               y=DP5['Casos activos por FIS'],
               mode='lines',
               name='Casos Activos FIS (DP5)',
               line_color=Wong[4]
              )
)
fig.update_layout(hovermode='x')
fig.update_layout(template='plotly_white',
                  title='Casos Activos de COVID19 en Chile')
fig.update_layout(yaxis_tickformat = ',')
fig.update_layout(
    font=dict(
        size=14,
    )
)

fig.write_html(f'{outputdir}/Casos_Activos.html')

fig = make_subplots(rows=2, shared_xaxes=True, specs=[[{"secondary_y": True}],[{"secondary_y": True}],], row_heights=[0.7, 0.3])
fig.add_trace(
    go.Scatter(x=casos_sintomaticos.index,
               y=casos_sintomaticos['Chile'].rolling(11).sum().rolling(7).mean(),
               mode='lines',
               name='Inferencia de activos (DP3)',
               line_color=Wong[1]
              )
    , row=1, col=1, secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=casos_uci.index,
               y=casos_uci['Chile'],
               mode='lines',
               name='Ocupación UCI (DP8)',
               line_color=Wong[2]
              )
    , row=1, col=1, secondary_y=True,
)
ucilag = 14
propuci = casos_uci['Chile'].shift(-ucilag)/casos_sintomaticos['Chile'].rolling(11).sum()
propuci_toto = casos_uci['Chile'].shift(-ucilag)/casos_nuevos_prob_antigeno['Chile'].rolling(11).sum()
prediccion_uci = casos_sintomaticos['Chile'].rolling(11).sum().rolling(7).mean()*0.066
prediccion_uci_toto = casos_nuevos_prob_antigeno['Chile'].rolling(11).sum().rolling(7).mean()*0.03771422787573839

prediccion_uci.index = prediccion_uci.index + pd.Timedelta(days=ucilag)
prediccion_uci_toto.index = prediccion_uci_toto.index + pd.Timedelta(days=ucilag)
fig.add_trace(
    go.Scatter(x=prediccion_uci.index,
               y=prediccion_uci,
               mode='lines',
               name='Ocupación UCI (predicción desde activos sintomaticos)',
               line_color=Wong[6],
               visible='legendonly'
              )
    , row=1, col=1, secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=prediccion_uci_toto.index,
               y=prediccion_uci_toto,
               mode='lines',
               name='Ocupación UCI (predicción desde total de activos)',
               line_color=Wong[7],
               visible='legendonly'
              )
    , row=1, col=1, secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=casos_uci.shift(-ucilag).index,
               y=casos_uci['Chile'].shift(-ucilag),
               mode='lines',
               name=f'Ocupación UCI (shift-{ucilag})',
               line_color=Wong[3],
               visible='legendonly'
              )
    , row=1, col=1, secondary_y=True,
)
fig.add_trace(
    go.Scatter(x=propuci.index,
               y=propuci.rolling(7).mean(),
               mode='lines',
               name=f'UCI (shift-{ucilag}) / Activos',
               line_color=Wong[0]
              )
    , row=2, col=1, secondary_y=False,
)
propuci_nolag = casos_uci['Chile']/casos_sintomaticos['Chile'].rolling(11).sum()
fig.add_trace(
    go.Scatter(x=propuci_nolag.index,
               y=propuci_nolag.rolling(7).mean(),
               mode='lines',
               name='UCI / Activos',
               line_color=Wong[4],
               visible='legendonly'

              )
    , row=2, col=1, secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=propuci_toto.index,
               y=propuci_toto.rolling(7).mean(),
               mode='lines',
               name='UCI / Activos (PCR + Probable + Antígeno)',
               line_color=Wong[7],
               visible='legendonly'

              )
    , row=2, col=1, secondary_y=False,
)
fig.update_layout(hovermode='x')

fig.update_layout(yaxis3_tickformat = '.1%')
fig.update_layout(yaxis1_tickformat = ',.0f')
fig.update_layout(yaxis2_tickformat = ',.0f')
fig.update_layout(template='plotly_white',
                  title='Incidencia del número de infectados activos en la utilización de UCIs')
fig.update_layout(
    font=dict(
        size=14,
    )
)

fig.update_yaxes(row=1, col=1, title_text='Casos activos')
fig.update_yaxes(row=1, col=1, title_text='Ocupación UCI', secondary_y=True)
fig.update_yaxes(row=2, col=1, title_text='UCI / Activos')

fig.write_html(f'{outputdir}/Casos_Activos_vs_UCI.html')
