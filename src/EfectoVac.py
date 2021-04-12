import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)
casos = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto16/CasosGeneroEtario_T.csv')
casos = casos.drop(0).rename(columns={'Grupo de edad': 'Fecha'}).set_index('Fecha')
casos_H = casos[casos.columns[:int(len(casos.columns)/2)]]
casos_M = casos[casos.columns[int(len(casos.columns)/2):]]
casos_M.columns= casos.columns[:int(len(casos.columns)/2)]
casos_H = casos_H.apply(pd.to_numeric)
casos_M = casos_M.apply(pd.to_numeric)
casos_m = casos_H + casos_M
casos_m.index = pd.to_datetime(casos_m.index)
# print(casos_m.index)
# hay un dia que no hubieron nuevos casos, borrando
casos_m = casos_m.drop(pd.Timestamp('2020-10-02'))
casos_m = casos_m.resample('D').interpolate('quadratic')
# casos_m = casos_m.resample('7D').sum().iloc[:-1].resample('1D').ffill().div(7).rolling(21).mean()

casos_m = casos_m.diff()
# hay un nuevo caso negativo, arreglando
casos_m.loc['2020-04-04']['00 - 04 años'] = 1
casos_m.loc['2020-04-05']['00 - 04 años'] = 0
casos_m_T = casos_m.T

uci = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto9/HospitalizadosUCIEtario_T.csv')
uci['Grupo de edad'] = pd.to_datetime(uci['Grupo de edad'],infer_datetime_format=True)
uci = uci.rename(columns={'Grupo de edad': 'Fecha'}).set_index('Fecha')
uci_T = uci.T

e0_39 = list(casos_m.columns[:8])
e40_49 = list(casos_m.columns[8:10])
e50_59 = list(casos_m.columns[10:12])
e60_69 = list(casos_m.columns[12:14])
e70_9999 = list(casos_m.columns[14:])
casos_m_edadesUCI = pd.merge(casos_m[e0_39].T.sum().rename('<=39'), casos_m[e40_49].T.sum().rename('40-49'), left_index=True, right_index=True)
casos_m_edadesUCI = pd.merge(casos_m_edadesUCI, casos_m[e50_59].T.sum().rename('50-59'), left_index=True, right_index=True)
casos_m_edadesUCI = pd.merge(casos_m_edadesUCI, casos_m[e60_69].T.sum().rename('60-69'), left_index=True, right_index=True)
casos_m_edadesUCI = pd.merge(casos_m_edadesUCI, casos_m[e70_9999].T.sum().rename('>=70'), left_index=True, right_index=True)
casos_m_edadesUCI_T = casos_m_edadesUCI.T


muertes = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto10/FallecidosEtario_T.csv')
muertes = muertes.rename(columns={'Grupo de edad': 'Fecha'}).set_index('Fecha')
muertes.index = pd.to_datetime(muertes.index)
muertes['>=70'] = muertes['70-79'] + muertes['80-89'] + muertes['>=90']
muertes = muertes.drop(columns=['70-79', '80-89', '>=90'])
muertes = muertes.drop(pd.Timestamp('2020-12-28')) # sin muertes
muertes = muertes.drop(pd.Timestamp('2021-01-04')) # sin muertes
# muertes = muertes.drop(pd.Timestamp('2020-07-19')) # raro
muertes = muertes.resample('D').interpolate()

muertes = muertes.diff()

muertes_T = muertes.T


#Ocupacion UCI
oc_uci = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto20/NumeroVentiladores_T.csv')
oc_uci = oc_uci.rename(columns={'Ventiladores': 'Fecha'}).set_index('Fecha')
oc_uci.loc['2020-09-30']['total'] = 2520
oc_uci = oc_uci.apply(pd.to_numeric)
oc_uci['%ocupacion'] = oc_uci['ocupados'] / oc_uci['total'] * 100
pl_casos = px.area(casos_m_edadesUCI.rolling(7).mean(), x=casos_m_edadesUCI.index, y=casos_m_edadesUCI.columns,
              labels={
                     "value": "Casos Diarios",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 7d de los casos nuevos de COVID19 nacional (Producto 16)")

pl_casos.update_layout(hovermode='x')
pl_casos.update_layout(legend_traceorder='reversed')
pl_casos.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.0f}",
    ])
)
pl_casos.update_layout(template='plotly_white')
pl_casos.update_layout(yaxis_tickformat = ',')
pl_casos.write_html(f'{outputdir}/casos_nuevos_por_edad.html')

pl_casos_p = px.area((casos_m_edadesUCI_T.div(casos_m_edadesUCI_T.sum())*100).T.rolling(7).mean(), x=casos_m_edadesUCI.index, y=casos_m_edadesUCI.columns,
              labels={
                     "value": "% Casos Diarios",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 7d de la proporción de casos nuevos de COVID19 nacional (%) (Producto 16)")

pl_casos_p.update_layout(hovermode='x')
pl_casos_p.update_layout(legend_traceorder='reversed')
pl_casos_p.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.1f}%",
    ])
)
pl_casos_p.update_layout(template='plotly_white')
pl_casos_p.update_layout(yaxis_tickformat = ',')

pl_casos_p.write_html(f'{outputdir}/casos_nuevos_por_edad_prop_stacked.html')

casos_m_p = (casos_m_edadesUCI_T.div(casos_m_edadesUCI_T.sum())*100).T
casos_m_p_prom = casos_m_p.expanding().mean()
casos_m_pp = casos_m_p.div(casos_m_p_prom)
casos_vs_prom = make_subplots(rows=5, cols=1, shared_xaxes=True,)

casos_vs_prom.append_trace(go.Scatter(
    x=casos_m_pp.index,
    y=casos_m_pp['>=70'].rolling(7).mean(), name='>=70'
), row=1, col=1)
casos_vs_prom.append_trace(go.Scatter(
    x=casos_m_pp.index,
    y=casos_m_pp['60-69'].rolling(7).mean(), name='60-69'
), row=2, col=1)
casos_vs_prom.append_trace(go.Scatter(
    x=casos_m_pp.index,
    y=casos_m_pp['50-59'].rolling(7).mean(), name='50-59'
), row=3, col=1)
casos_vs_prom.append_trace(go.Scatter(
    x=casos_m_pp.index,
    y=casos_m_pp['40-49'].rolling(7).mean(), name='40-49'
), row=4, col=1)
casos_vs_prom.append_trace(go.Scatter(
    x=casos_m_pp.index,
    y=casos_m_pp['<=39'].rolling(7).mean(), name='<=39'
), row=5, col=1)

casos_vs_prom.update_layout(title_text="Media móvil 7d de la variación contra el promedio acumulado diario<br>de la proporción de casos nuevos de COVID19 nacional (Producto 16)")
casos_vs_prom.update_yaxes(range=[casos_m_pp.rolling(7).mean().min().min(), casos_m_pp.rolling(7).mean().max().max()],)
casos_vs_prom.update_layout(hovermode='x')
casos_vs_prom.add_hline(y=1)
casos_vs_prom.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.3f}",
    ])
)
casos_vs_prom.update_layout(template='plotly_white')
casos_vs_prom.update_layout(yaxis_tickformat = ',')

casos_vs_prom.write_html(f'{outputdir}/casos_vs_prom.html')

casos_m_p_all = (casos_m_T.div(casos_m_T.sum())*100).T
casos_m_p_all_prom = casos_m_p_all.expanding().mean()[casos_m_p_all.columns[:8]]
casos_m_pp_all = casos_m_p_all.div(casos_m_p_all_prom)
casos_vs_prom_all = make_subplots(rows=8, cols=1, shared_xaxes=True,)

for fila, edad in enumerate(list(casos_m.columns[:8])[::-1], 1):
#     print(fila,edad)
    casos_vs_prom_all.append_trace(go.Scatter(
        x=casos_m_pp_all.index,
        y=casos_m_pp_all[edad].rolling(7).mean(), name=edad
    ), row=fila, col=1)
casos_vs_prom_all.update_layout(title_text="Media móvil 7d de la variación contra el promedio acumulado diario<br>de la proporción de casos nuevos de COVID19 nacional (Producto 16)")
casos_vs_prom_all.update_yaxes(range=[casos_m_pp_all.rolling(7).mean().min().min(), casos_m_pp_all.rolling(7).mean().max().max()],)
casos_vs_prom_all.update_layout(hovermode='x')
# casos_vs_prom_all.update_layout(height=1500)
casos_vs_prom_all.add_hline(y=1)
casos_vs_prom_all.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.3f}",
    ])
)
casos_vs_prom_all.update_layout(template='plotly_white')
casos_vs_prom_all.update_layout(yaxis_tickformat = ',')

casos_vs_prom_all.write_html(f'{outputdir}/casos_vs_prom_todas_las_edades.html')

pl_UCI = px.area(uci.rolling(7).mean(), x=uci.index, y=uci.columns,
              labels={
                     "value": "Ocupación UCI",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 7d de la ocupación UCI de casos COVID19 nacional (Producto 9)")

pl_UCI.update_layout(hovermode='x')
pl_UCI.update_layout(legend_traceorder='reversed')
pl_UCI.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.0f}",
    ])
)
pl_UCI.update_layout(template='plotly_white')
pl_UCI.update_layout(yaxis_tickformat = ',')

pl_UCI.write_html(f'{outputdir}/ocupacion_UCI_por_edad.html')

pl_UCI_p = px.area((uci_T.div(uci_T.sum())*100).T.rolling(7).mean(), x=uci.index, y=uci.columns,
              labels={
                     "value": "% Ocupación UCI",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 7d de la ocupación UCI de casos COVID19 nacional (%) (Producto 9)")

pl_UCI_p.update_layout(hovermode='x')
pl_UCI_p.update_layout(legend_traceorder='reversed')
pl_UCI_p.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.1f}%",
    ])
)
pl_UCI.update_layout(template='plotly_white')
pl_UCI.update_layout(yaxis_tickformat = ',')

pl_UCI.write_html(f'{outputdir}/ocupacion_UCI_por_edad_prop_stacked.html')

uci_p = (uci_T.div(uci_T.sum())*100).T
uci_p_prom = uci_p.expanding().mean()
uci_pp = uci_p.div(uci_p_prom)
uci_vs_prom = make_subplots(rows=6, cols=1, shared_xaxes=True,specs=[[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],])
uci_vs_prom.append_trace(go.Scatter(
    x=uci_pp.index,
    y=uci_pp['>=70'].rolling(7).mean(), name='>=70'
), row=1, col=1)
uci_vs_prom.append_trace(go.Scatter(
    x=uci_pp.index,
    y=uci_pp['60-69'].rolling(7).mean(), name='60-69'
), row=2, col=1)
uci_vs_prom.append_trace(go.Scatter(
    x=uci_pp.index,
    y=uci_pp['50-59'].rolling(7).mean(), name='50-59'
), row=3, col=1)
uci_vs_prom.append_trace(go.Scatter(
    x=uci_pp.index,
    y=uci_pp['40-49'].rolling(7).mean(), name='40-49'
), row=4, col=1)
uci_vs_prom.append_trace(go.Scatter(
    x=uci_pp.index,
    y=uci_pp['<=39'].rolling(7).mean(), name='<=39'
), row=5, col=1)
uci_vs_prom.add_hline(y=1)
uci_vs_prom.append_trace(go.Scatter(
    x=oc_uci['%ocupacion'].index,
    y=oc_uci['%ocupacion'].rolling(7).mean(), name='% Ocupación UCI (Producto 20)'
), row=6, col=1)
uci_vs_prom.add_trace(go.Scatter(
    x=muertes_T.sum().T.rolling(14).mean().index,
    y=muertes_T.sum().T.rolling(14).mean(), name='Fallecidos diarios (Producto 10)'
), row=6, col=1, secondary_y=True)

uci_vs_prom.update_layout(title_text="Media móvil 7d de la variación contra el promedio acumulado diario<br>de la proporción de ocupación UCI de COVID19 nacional (Producto 9)")
uci_vs_prom.update_yaxes(range=[uci_pp.rolling(7).mean().min().min(), uci_pp.rolling(7).mean().max().max()],)
uci_vs_prom.update_yaxes(range=[50,100], row=6, col=1, title_text=" % Ocupación UCI", secondary_y=False)
uci_vs_prom.update_yaxes(range=[0,200], row=6, col=1, title_text="Fallecidos diarios", secondary_y=True)
uci_vs_prom.update_layout(hovermode='x')
uci_vs_prom.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.3f}",
    ])
)
uci_vs_prom.update_layout(template='plotly_white')
uci_vs_prom.update_layout(yaxis_tickformat = ',')

uci_vs_prom.write_html(f'{outputdir}/uci_vs_prom.html')

pl_muertes = px.area(muertes.rolling(14).mean(), x=muertes.index, y=uci.columns,
              labels={
                     "value": "Fallecidos",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 7d del fallecimiento de casos COVID19 nacional (Producto 10)")

pl_muertes.update_layout(hovermode='x')
pl_muertes.update_layout(legend_traceorder='reversed')
pl_muertes.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.0f}",
    ])
)
pl_muertes.update_layout(template='plotly_white')
pl_muertes.update_layout(yaxis_tickformat = ',')

pl_muertes.write_html(f'{outputdir}/fallecidos_nuevos_por_edad.html')

pl_muertes_p = px.area((muertes_T.div(muertes_T.sum())*100).T.rolling(14).mean(), x=muertes.index, y=muertes.columns,
              labels={
                     "value": "% Fallecidos",
                     "x": "Día",
                     "variable": "Rango etario"
              },
              title="Media móvil 14d de la proporción de fallecimiento de casos COVID19 nacional (%) (Producto 10)")

pl_muertes_p.update_layout(hovermode='x')
pl_muertes_p.update_layout(legend_traceorder='reversed')
pl_muertes_p.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.1f}%",
    ])
)
pl_muertes_p.update_layout(template='plotly_white')
pl_muertes_p.update_layout(yaxis_tickformat = ',')

pl_muertes_p.write_html(f'{outputdir}/fallecidos_nuevos_por_edad_prop_stacked.html')

muertes_p = (muertes_T.div(muertes_T.sum())*100).T
muertes_p_prom = muertes_p.expanding().mean()
muertes_pp = muertes_p.div(muertes_p_prom)
muertes_vs_prom = make_subplots(rows=6, cols=1, shared_xaxes=True,specs=[[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],[{"secondary_y": True}],])

muertes_vs_prom.append_trace(go.Scatter(
    x=muertes_pp.index,
    y=muertes_pp['>=70'].rolling(14).mean(), name='>=70'
), row=1, col=1)
muertes_vs_prom.append_trace(go.Scatter(
    x=muertes_pp.index,
    y=muertes_pp['60-69'].rolling(14).mean(), name='60-69'
), row=2, col=1)
muertes_vs_prom.append_trace(go.Scatter(
    x=muertes_pp.index,
    y=muertes_pp['50-59'].rolling(14).mean(), name='50-59'
), row=3, col=1)
muertes_vs_prom.append_trace(go.Scatter(
    x=muertes_pp.index,
    y=muertes_pp['40-49'].rolling(14).mean(), name='40-49'
), row=4, col=1)
muertes_vs_prom.append_trace(go.Scatter(
    x=muertes_pp.index,
    y=muertes_pp['<=39'].rolling(14).mean(), name='<=39'
), row=5, col=1)
muertes_vs_prom.add_hline(y=1)
muertes_vs_prom.append_trace(go.Scatter(
    x=oc_uci['%ocupacion'].index,
    y=oc_uci['%ocupacion'].rolling(14).mean(), name='% Ocupacion UCI (Producto 20)'
), row=6, col=1)
muertes_vs_prom.add_trace(go.Scatter(
    x=muertes_T.sum().T.rolling(14).mean().index,
    y=muertes_T.sum().T.rolling(14).mean(), name='Fallecidos diarios (Producto 10)'
), row=6, col=1, secondary_y=True)
# muertes_T.sum().T.rolling(14).mean().plot()
muertes_vs_prom.update_layout(title_text="Media móvil 14d de la variación contra el promedio acumulado diario<br>de la proporción de los fallecidos de COVID19 nacional (Producto 10)")
muertes_vs_prom.update_yaxes(range=[muertes_pp.rolling(14).mean().min().min(), muertes_pp.rolling(14).mean().max().max()],)
muertes_vs_prom.update_yaxes(range=[50,100], row=6, col=1, title_text=" % Ocupación UCI", secondary_y=False)
muertes_vs_prom.update_yaxes(range=[0,200], row=6, col=1, title_text="Fallecidos diarios", secondary_y=True)
muertes_vs_prom.update_layout(hovermode='x')
muertes_vs_prom.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.3f}",
    ])
)
muertes_vs_prom.update_layout(template='plotly_white')
muertes_vs_prom.update_layout(yaxis_tickformat = ',')

muertes_vs_prom.write_html(f'{outputdir}/fallecidos_vs_prom.html')

#Vacunas
piramide_chile = {
    '>=70': 1473727,
    '60-69': 1737346,
    '50-59': 2328585,
    '40-49': 2556775,
    '<=39': 10855602,
}
vac = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto76/rango_etario_t.csv')
vac_1 = vac[['Rango_etario', '15-20','21-30','31-40','41-50','51-60','61-70','71-72','73-74','75-77','78-79','80 y más']].drop([0,1,2])
vac_2 = vac[['Rango_etario', '15-20.1', '21-30.1', '31-40.1', '41-50.1', '51-60.1', '61-70.1', '71-72.1', '73-74.1', '75-77.1', '78-79.1', '80 y más.1']].drop([0,1,2])
vac_2.columns = vac_1.columns
vac_1 = vac_1.rename(columns={'Rango_etario': 'Fecha'}).set_index('Fecha')
vac_2 = vac_2.rename(columns={'Rango_etario': 'Fecha'}).set_index('Fecha')
vac_1 = vac_1.apply(pd.to_numeric)
vac_2 = vac_2.apply(pd.to_numeric)

vac_1['>=71'] = vac_1['71-72'] + vac_1['73-74'] + vac_1['75-77'] + vac_1['78-79'] + vac_1['80 y más'] 
vac_2['>=71'] = vac_2['71-72'] + vac_2['73-74'] + vac_2['75-77'] + vac_2['78-79'] + vac_2['80 y más']
vac_1['<=40'] = vac_1['15-20'] + vac_1['21-30'] + vac_1['31-40']
vac_2['<=40'] = vac_2['15-20'] + vac_2['21-30'] + vac_2['31-40']
# vac_1.drop(columns=['15-20','21-30','31-40','41-50','51-60','61-70','71-72','73-74','75-77','78-79','80 y más'], inplace=True)
# vac_2.drop(columns=['15-20','21-30','31-40','41-50','51-60','61-70','71-72','73-74','75-77','78-79','80 y más'], inplace=True)
vac_1['>=71'] = vac_1['>=71']/piramide_chile['>=70']*100
vac_2['>=71'] = vac_2['>=71']/piramide_chile['>=70']*100
vac_1['61-70'] = vac_1['61-70']/piramide_chile['60-69']*100
vac_2['61-70'] = vac_2['61-70']/piramide_chile['60-69']*100
vac_1['51-60'] = vac_1['51-60']/piramide_chile['50-59']*100
vac_2['51-60'] = vac_2['51-60']/piramide_chile['50-59']*100
vac_1['41-50'] = vac_1['41-50']/piramide_chile['40-49']*100
vac_2['41-50'] = vac_2['41-50']/piramide_chile['40-49']*100
vac_1['<=40'] = vac_1['<=40']/piramide_chile['<=39']*100
vac_2['<=40'] = vac_2['<=40']/piramide_chile['<=39']*100
pl_vac_tot = make_subplots(rows=5, cols=1, shared_xaxes=True,)

pl_vac_tot.append_trace(go.Scatter(
    x=vac_1.index,
    y=vac_1['>=71'].rolling(7).mean(), name='Primera dosis >=71'
), row=1, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_1.index,
    y=vac_1['61-70'].rolling(7).mean(), name='Primera dosis 61-70'
), row=2, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_1.index,
    y=vac_1['51-60'].rolling(7).mean(), name='Primera dosis 51-60'
), row=3, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_1.index,
    y=vac_1['41-50'].rolling(7).mean(), name='Primera dosis 41-50'
), row=4, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_1.index,
    y=vac_1['<=40'].rolling(7).mean(), name='Primera dosis <=40'
), row=5, col=1)


pl_vac_tot.append_trace(go.Scatter(
    x=vac_2.index,
    y=vac_2['>=71'].rolling(7).mean(), name='Segunda dosis >=71',
    line=dict(dash='dash')
), row=1, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_2.index,
    y=vac_2['61-70'].rolling(7).mean(), name='Segunda dosis 61-70',
    line=dict(dash='dash')
), row=2, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_2.index,
    y=vac_2['51-60'].rolling(7).mean(), name='Segunda dosis 50-59',
    line=dict(dash='dash')
), row=3, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_2.index,
    y=vac_2['41-50'].rolling(7).mean(), name='Segunda dosis 41-50',
    line=dict(dash='dash')
), row=4, col=1)
pl_vac_tot.append_trace(go.Scatter(
    x=vac_2.index,
    y=vac_2['<=40'].rolling(7).mean(), name='Segunda dosis <=40',
    line=dict(dash='dash')
), row=5, col=1)


pl_vac_tot.update_layout(title_text="Media móvil 7d de la proporción de vacunados en Chile con la primera dosis (Producto 76)")
pl_vac_tot.update_yaxes(range=[0,100],)
pl_vac_tot.update_layout(hovermode='x')
# pl_vac_1.add_hline(y=1)
pl_vac_tot.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.1f}%",
    ])
)
pl_vac_tot.update_layout(template='plotly_white')
pl_vac_tot.update_layout(yaxis_tickformat = ',')

pl_vac_tot.write_html(f'{outputdir}/vacunacion_total.html')