import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

repo_dir = Path(__file__).parent.parent
csvoutputdir = repo_dir/'csv_output'
csvoutputdir.mkdir(parents=True, exist_ok=True)
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)

piramide_chile_INE = { # INE - Proyección base 2017
    '>=70': 1_614_364,
    '60-69': 1_857_879,
    '50-59': 2_392_614,
    '40-49': 2_658_453,
    '<=39': 11_155_053,
}
dosis2 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto78/vacunados_edad_fecha_2daDosis_std.csv', parse_dates=[1],)
bins = [0, 40, 50, 60, 70, 999]
labels = ['<=39', '40-49', '50-59', '60-69', '>=70']
dosis2['agerange'] = pd.cut(dosis2.Edad, bins, labels=labels, include_lowest=True, right=False)
dosis2 = pd.pivot_table(dosis2, values=['Segunda Dosis'], index=['Fecha'],
                    columns=['agerange'], aggfunc=np.sum)['Segunda Dosis']
monodosis = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto78/vacunados_edad_fecha_UnicaDosis_std.csv', parse_dates=[1],)
monodosis['agerange'] = pd.cut(monodosis.Edad, bins, labels=labels, include_lowest=True, right=False)
monodosis = pd.pivot_table(monodosis, values=['Unica Dosis'], index=['Fecha'],
                    columns=['agerange'], aggfunc=np.sum)['Unica Dosis']
esquema_completo = dosis2.shift(14) + monodosis.shift(28)
esquema_completo = esquema_completo.cumsum()
p_esquema_completo = esquema_completo.copy()
p_esquema_completo['>=70'] = p_esquema_completo['>=70']/piramide_chile_INE['>=70']*100
p_esquema_completo['60-69'] = p_esquema_completo['60-69']/piramide_chile_INE['60-69']*100
p_esquema_completo['50-59'] = p_esquema_completo['50-59']/piramide_chile_INE['50-59']*100
p_esquema_completo['40-49'] = p_esquema_completo['40-49']/piramide_chile_INE['40-49']*100
p_esquema_completo['<=39'] = p_esquema_completo['<=39']/piramide_chile_INE['<=39']*100

etiquetas = {
    'value': 'Porcentaje de la población',
    'agerange': 'Rango etario'
}
pl_esq_com = px.line(p_esquema_completo, labels=etiquetas)
pl_esq_com.update_layout(title_text="Porcentaje de la población con esquema de vacunación completo (Producto 78)")
pl_esq_com.update_yaxes(range=[0,100],)
pl_esq_com.update_layout(hovermode='x')
pl_esq_com.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.1f}%",
    ])
)
pl_esq_com.update_layout(template='plotly_white')
# pl_vac_tot.update_layout(yaxis_tickformat = ',.1f')
pl_esq_com.update_layout(
    font=dict(
        size=14,
    )
)
pl_esq_com.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.00,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
pl_esq_com.write_html(f'{outputdir}/EsquemaCompleto.html')

pd.melt(p_esquema_completo, ignore_index=False, var_name='agerange', value_name='Porcentaje de la población').to_csv(f'{csvoutputdir}/EsquemaCompletoPorcentaje_std.csv')
pd.melt(esquema_completo, ignore_index=False, var_name='agerange', value_name='Población').to_csv(f'{csvoutputdir}/EsquemaCompleto_std.csv')
