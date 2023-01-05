import pandas as pd
import numpy as np
import urllib.request
from zipfile import ZipFile
from re import compile
from pathlib import Path
from shutil import rmtree
import plotly.express as px

repo_dir = Path(__file__).parent.parent
csvoutputdir = repo_dir/'csv_output'
csvoutputdir.mkdir(parents=True, exist_ok=True)
outputdir = repo_dir/'output'
outputdir.mkdir(parents=True, exist_ok=True)
deis_data = repo_dir/'deis_data'
deis_data.mkdir(parents=True, exist_ok=True)

def get_deis_death_url():
    datapattern = compile('http.*DEFUNCIONES_FUENTE_DEIS.*zip\"\\n\"tags\":\"defunciones\"')
    with urllib.request.urlopen('https://deis.minsal.cl/wp-admin/admin-ajax.php?action=wp_ajax_ninja_tables_public_action&table_id=2889&target_action=get-all-data&default_sorting=manual_sort') as f:
        return datapattern.search(f.read().decode().replace(',','\n')).group().replace('\\', '').split('"')[0]

def get_csv_deis():
    url = get_deis_death_url()
    urllib.request.urlretrieve(url, 'deis_data/' + url.split('/')[-1])
    with ZipFile('deis_data/' + url.split('/')[-1], 'r') as rar_ref:
        rar_ref.extractall('deis_data')
    return url.split('/')[-1][:-3]

def annos(row):
    edad = row['EDAD_CANT']
    tipo = row['EDAD_TIPO']
    if tipo == 1:
        return edad
    elif tipo == 2:
        return edad/12
    elif tipo == 3:
        return edad/365
    elif tipo == 4:
        return edad/365*24
    else:
        return np.nan
deis_csv = 'deis_data/' + get_csv_deis() + 'csv'

# INE - Proyección base 2017
piramide = {
    '<=19': 4_988_470,
    '20-29': 3_046_000,
    '30-39': 3_120_583,
    '40-49': 2_658_453,
    '50-59': 2_392_614,
    '60-69': 1_857_879,
    '70-79': 1_046_294,
    '>=80': 568_070,
}
columnas = ['ANO_DEF', 'FECHA_DEF', 'GLOSA_SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'CODIGO_COMUNA_RESIDENCIA', 'GLOSA_COMUNA_RESIDENCIA', 'GLOSA_REG_RES', 'DIAG1', 'CAPITULO_DIAG1', 'GLOSA_CAPITULO_DIAG1', 'CODIGO_GRUPO_DIAG1', 'GLOSA_GRUPO_DIAG1', 'CODIGO_CATEGORIA_DIAG1', 'GLOSA_CATEGORIA_DIAG1', 'CODIGO_SUBCATEGORIA_DIAG1', 'GLOSA_SUBCATEGORIA_DIAG1', 'DIAG2', 'CAPITULO_DIAG2', 'GLOSA_CAPITULO_DIAG2', 'CODIGO_GRUPO_DIAG2', 'GLOSA_GRUPO_DIAG2', 'CODIGO_CATEGORIA_DIAG2', 'GLOSA_CATEGORIA_DIAG2', 'CODIGO_SUBCATEGORIA_DIAG2', 'GLOSA_SUBCATEGORIA_DIAG2', 'LUGAR_DEFUNCION']
deis = pd.read_csv(deis_csv, sep=';', parse_dates=[1], header=None, names=columnas, index_col=False, encoding='latin-1')
deis.set_index(['FECHA_DEF'], inplace=True)
deis.sort_index(inplace=True)
# CODIGO_CATEGORIA_DIAG1 U07 > covid19
rmtree('deis_data')
deis['EDAD_ANOS'] = deis.apply(annos, axis = 1)
bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 999]
bins_10s = [0, 10, 20, 30, 40, 50, 60, 70, 80, 999]
labels = ['00-04', '05-09', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', '80+']
labels_10s = ['00-09', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
deis['agerange'] = pd.cut(deis.EDAD_ANOS, bins, labels=labels, include_lowest=True, right=False)
deis['agerange_10s'] = pd.cut(deis.EDAD_ANOS, bins_10s, labels=labels_10s, include_lowest=True, right=False)
# deis_gruped = pd.pivot_table(deis.loc[(deis['CODIGO_CATEGORIA_DIAG1'] == 'U07')], values=['EDAD_CANT'], index=['FECHA_DEF'],
#                     columns=['agerange'], aggfunc='count')['EDAD_CANT']
# deis_gruped = deis_gruped.resample('D').asfreq().fillna(0)
# deis_gruped
defunciones_deis_genero_edad = pd.pivot_table(deis.loc[(deis['CODIGO_CATEGORIA_DIAG1'] == 'U07')], values=['EDAD_CANT'], index=['FECHA_DEF'],
                    columns=['GLOSA_SEXO', 'agerange'], aggfunc='count')['EDAD_CANT']
defunciones_deis_genero_edad.columns.names = ['Sexo', 'Edad']
defunciones_deis_genero_edad.index.name = 'Fecha'
defunciones_deis_genero_edad = defunciones_deis_genero_edad.asfreq('D').fillna(0)

defunciones_deis_genero_edad_10s = pd.pivot_table(deis.loc[(deis['CODIGO_CATEGORIA_DIAG1'] == 'U07')], values=['EDAD_CANT'], index=['FECHA_DEF'],
                    columns=['GLOSA_SEXO', 'agerange_10s'], aggfunc='count')['EDAD_CANT']
defunciones_deis_genero_edad_10s.columns.names = ['Sexo', 'Edad']
defunciones_deis_genero_edad_10s.index.name = 'Fecha'
defunciones_deis_genero_edad_10s = defunciones_deis_genero_edad_10s.asfreq('D').fillna(0)
casos = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto16/CasosGeneroEtario_std.csv')
tr_edad = {
    '00 - 04 años': '00-04',
    '05 - 09 años': '05-09',
    '10 - 14 años': '10-14',
    '15 - 19 años': '15-19',
    '20 - 24 años': '20-24',
    '25 - 29 años': '25-29',
    '30 - 34 años': '30-34',
    '35 - 39 años': '35-39',
    '40 - 44 años': '40-44',
    '45 - 49 años': '45-49',
    '50 - 54 años': '50-54',
    '55 - 59 años': '55-59',
    '60 - 64 años': '60-64',
    '65 - 69 años': '65-69',
    '70 - 74 años': '70-74',
    '75 - 79 años': '75-79',
    '80 y más años': '80+'
}
tr_sex ={
    'M': 'Hombre',
    'F': 'Mujer'
}
casos['Grupo de edad'].replace(tr_edad, inplace=True)
casos['Sexo'].replace(tr_sex, inplace=True)
casos['Fecha'] = pd.to_datetime(casos['Fecha'])
casos_genero_edad = pd.pivot_table(casos, values=['Casos confirmados'], index=['Fecha'],
                    columns=['Sexo', 'Grupo de edad'])['Casos confirmados']
# hay un dia que no hubieron nuevos casos, borrando
casos_genero_edad = casos_genero_edad.drop(pd.Timestamp('2020-10-02'))
casos_genero_edad = casos_genero_edad.resample('D').interpolate('quadratic')
casos_genero_edad = casos_genero_edad.diff().fillna(0)

casos_genero_edad.columns.names = ['Sexo', 'Edad']
# casos_genero_edad.index.name = 'Fecha'
casos_genero_edad_10s = casos_genero_edad.copy()
i = 0
for sex in tr_sex.values():
    for ages in labels_10s:
        if ages == '80+':
#             casos_genero_edad_10s[sex, ages] = casos_genero_edad_10s[sex]['80+']
            continue
#         print(casos_genero_edad_10s[sex].columns[i:i+2])
#         print(casos_genero_edad_10s[sex][casos_genero_edad_10s[sex].columns[i:i+2]].sum())
        casos_genero_edad_10s[sex, ages] = casos_genero_edad_10s[sex][casos_genero_edad_10s[sex].columns[i:i+2]].sum(axis=1)
        i += 2
    i = 0
casos_genero_edad_10s.drop(columns=list(tr_edad.values())[:-1], inplace=True, level=1)
casos_genero_edad_10s = casos_genero_edad_10s.sort_index(axis=1)
defunciones_deis_edad = defunciones_deis_genero_edad.sum().reset_index().groupby(['Edad']).sum()
casos_edad = casos_genero_edad.sum().reset_index().groupby(['Edad']).sum()
cfr_edad = defunciones_deis_edad/casos_edad
cfr_edad.rename(columns={0: 'CFR'}, inplace=True)
cfr_edad = cfr_edad.reset_index()
overall_ing = 'General'
cfr_edad['Sexo'] = overall_ing

cfr = ((defunciones_deis_genero_edad.sum()/casos_genero_edad.sum()))
cfr.rename('CFR', inplace=True)
cfr = cfr.reset_index()

cfr_total_total = defunciones_deis_genero_edad.sum().sum()/casos_genero_edad.sum().sum()
cfr_total_hombre = defunciones_deis_genero_edad['Hombre'].sum().sum()/casos_genero_edad['Hombre'].sum().sum()
cfr_total_mujer = defunciones_deis_genero_edad['Mujer'].sum().sum()/casos_genero_edad['Mujer'].sum().sum()
cfr = cfr.append({'Sexo': 'Hombre', 'Edad': overall_ing, 'CFR': cfr_total_hombre}, ignore_index=True)
cfr = cfr.append({'Sexo': 'Mujer', 'Edad': overall_ing, 'CFR': cfr_total_mujer}, ignore_index=True)
cfr = cfr.append({'Sexo': overall_ing, 'Edad': overall_ing, 'CFR': cfr_total_total}, ignore_index=True)
cfr = cfr.append(cfr_edad, ignore_index=True)
Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']

fig_cfr = px.bar(
    cfr,
    x='Edad',
    y='CFR',
    color='Sexo',
    barmode='group',
    text='CFR',
    color_discrete_sequence=Wong
)
fig_cfr.update_xaxes(type='category')
fig_cfr.update_layout(hovermode='x')
fig_cfr.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.2%}",
    ])
)
fig_cfr.update_layout(
    template='plotly_white',
    yaxis_tickformat = '.1%',
    font=dict(
        size=14,
    ),
    title='Tasa de letalidad por COVID19 en Chile (Case Fatality Rate, CFR)'
)
fig_cfr.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.0,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
# fig_cfr.update_layout(
#        updatemenus=[
#             dict(
#                  buttons=[
#                      dict(label="Lineal",  
#                           method="relayout", 
#                           args=[{"yaxis.type": "linear"}]),
#                      dict(label="logarítmico", 
#                           method="relayout", 
#                           args=[{"yaxis.type": "log"}]),
#                                   ])],
#                 font=dict(size=11)
#             )
fig_cfr.update_traces(texttemplate='%{text:.1%}', textposition='outside')
fig_cfr.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

fig_cfr.write_html(f'{outputdir}/CFR_edad_sexo.html')
cfr.to_csv(f'{csvoutputdir}/CFR_edad_sexo_std.csv', index=False)


defunciones_deis_edad_10s = defunciones_deis_genero_edad_10s.sum().reset_index().groupby(['Edad']).sum()
casos_edad_10s = casos_genero_edad_10s.sum().reset_index().groupby(['Edad']).sum()
cfr_edad_10s = defunciones_deis_edad_10s/casos_edad_10s
cfr_edad_10s.rename(columns={0: 'CFR'}, inplace=True)
cfr_edad_10s = cfr_edad_10s.reset_index()
overall_ing = 'General'
cfr_edad_10s['Sexo'] = overall_ing

cfr_10s = ((defunciones_deis_genero_edad_10s.sum()/casos_genero_edad_10s.sum()))
cfr_10s.rename('CFR', inplace=True)
cfr_10s = cfr_10s.reset_index()

cfr_total_total_10s = defunciones_deis_genero_edad_10s.sum().sum()/casos_genero_edad_10s.sum().sum()
cfr_total_hombre_10s = defunciones_deis_genero_edad_10s['Hombre'].sum().sum()/casos_genero_edad_10s['Hombre'].sum().sum()
cfr_total_mujer_10s = defunciones_deis_genero_edad_10s['Mujer'].sum().sum()/casos_genero_edad_10s['Mujer'].sum().sum()
cfr_10s = cfr_10s.append({'Sexo': 'Hombre', 'Edad': overall_ing, 'CFR': cfr_total_hombre_10s}, ignore_index=True)
cfr_10s = cfr_10s.append({'Sexo': 'Mujer', 'Edad': overall_ing, 'CFR': cfr_total_mujer_10s}, ignore_index=True)
cfr_10s = cfr_10s.append({'Sexo': overall_ing, 'Edad': overall_ing, 'CFR': cfr_total_total_10s}, ignore_index=True)
cfr_10s = cfr_10s.append(cfr_edad_10s, ignore_index=True)

Wong = ['#000000', '#E69F00', '#56B4E9',
        '#009E73', '#F0E442', '#0072B2',
        '#D55E00', '#CC79A7']

fig_cfr_10s = px.bar(
    cfr_10s,
    x='Edad',
    y='CFR',
    color='Sexo',
    barmode='group',
    color_discrete_sequence=Wong
)
fig_cfr_10s.update_xaxes(type='category')
fig_cfr_10s.update_layout(hovermode='x')
fig_cfr_10s.update_traces(
    hovertemplate="<br>".join([
#         "Día: %{x}",
        "%{y:.2%}",
    ])
)
fig_cfr_10s.update_layout(
    template='plotly_white',
    yaxis_tickformat = '.1%',
    font=dict(
        size=14,
    ),
    title='Tasa de letalidad por COVID19 en Chile (Case Fatality Rate, CFR)'
)
fig_cfr_10s.add_layout_image(
    dict(
        source="https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png",
        xref="paper", yref="paper",
        x=1, y=1.0,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
    )
)
# fig_cfr_10s.update_layout(
#        updatemenus=[
#             dict(
#                  buttons=[
#                      dict(label="Lineal",  
#                           method="relayout", 
#                           args=[{"yaxis.type": "linear"}]),
#                      dict(label="Logaritmico", 
#                           method="relayout", 
#                           args=[{"yaxis.type": "log"}]),
#                                   ])],
#                 font=dict(size=11)
#             )
fig_cfr_10s.write_html(f'{outputdir}/CFR_edad_sexo_10s.html')
cfr_10s.to_csv(f'{csvoutputdir}/CFR_edad_sexo_std_10s.csv', index=False)

