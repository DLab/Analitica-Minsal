import pandas as pd
import numpy as np
import urllib.request
from zipfile import ZipFile
from re import compile
from pathlib import Path
from shutil import rmtree
import os

repo_dir = Path(__file__).parent.parent
outputdir = repo_dir/'csv_output'
outputdir.mkdir(parents=True, exist_ok=True)
deis_data = repo_dir/'deis_data'
deis_data.mkdir(parents=True, exist_ok=True)

def get_deis_death_url():
    datapattern = compile('http.*DEFUNCIONES_FUENTE_DEIS_2016_2021.*zip')
    with urllib.request.urlopen('https://deis.minsal.cl/wp-admin/admin-ajax.php?action=wp_ajax_ninja_tables_public_action&table_id=2889&target_action=get-all-data&default_sorting=manual_sort') as f:
        return datapattern.search(f.read().decode().replace(',','\n')).group().replace('\\', '')

def get_csv_deis():
    url = get_deis_death_url()
    urllib.request.urlretrieve(url, 'deis_data/'+url.split('/')[-1])
    with ZipFile('deis_data/' + url.split('/')[-1], 'r') as zip_ref:
        zip_ref.extractall('deis_data')
    return url.split('/')[-1][:-4]

deis_csv = 'deis_data/' + get_csv_deis() + '.csv'
print(f'deis_data/{get_csv_deis()}.zip')

print(deis_csv)

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
casos_m['>=80'] = casos_m[casos_m.columns[-1]]
casos_m['70-79'] = casos_m[casos_m.columns[14:16]].sum(axis=1)
casos_m['60-69'] = casos_m[casos_m.columns[12:14]].sum(axis=1)
casos_m['50-59'] = casos_m[casos_m.columns[10:12]].sum(axis=1)
casos_m['40-49'] = casos_m[casos_m.columns[8:10]].sum(axis=1)
casos_m['30-39'] = casos_m[casos_m.columns[6:8]].sum(axis=1)
casos_m['20-29'] = casos_m[casos_m.columns[4:6]].sum(axis=1)
casos_m['<=19'] = casos_m[casos_m.columns[:4]].sum(axis=1)
casos_m.drop(columns=casos_m.columns[:17], inplace=True)
dosis2 = pd.read_csv('https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto78/vacunados_edad_fecha_2daDosis_T.csv', index_col=0)
dosis2.fillna(0, inplace=True)
dosis2['>=80'] = dosis2[dosis2.columns[62:]].sum(axis=1)
dosis2['70-79'] = dosis2[dosis2.columns[52:62]].sum(axis=1)
dosis2['60-69'] = dosis2[dosis2.columns[42:52]].sum(axis=1)
dosis2['50-59'] = dosis2[dosis2.columns[32:42]].sum(axis=1)
dosis2['40-49'] = dosis2[dosis2.columns[22:32]].sum(axis=1)
dosis2['30-39'] = dosis2[dosis2.columns[12:22]].sum(axis=1)
dosis2['20-29'] = dosis2[dosis2.columns[2:12]].sum(axis=1)
dosis2['<=19'] = dosis2[dosis2.columns[:3]].sum(axis=1)
dosis2.drop(columns=dosis2.columns[:-8], inplace=True)
dosis2.index = pd.to_datetime(dosis2.index)

columnas = ['ANO_DEF', 'FECHA_DEF', 'GLOSA_SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'CODIGO_COMUNA_RESIDENCIA', 'GLOSA_COMUNA_RESIDENCIA', 'GLOSA_REG_RES', 'DIAG1', 'CAPITULO_DIAG1', 'GLOSA_CAPITULO_DIAG1', 'CODIGO_GRUPO_DIAG1', 'GLOSA_GRUPO_DIAG1', 'CODIGO_CATEGORIA_DIAG1', 'GLOSA_CATEGORIA_DIAG1', 'CODIGO_SUBCATEGORIA_DIAG1', 'GLOSA_SUBCATEGORIA_DIAG1', 'DIAG2', 'CAPITULO_DIAG2', 'GLOSA_CAPITULO_DIAG2', 'CODIGO_GRUPO_DIAG2', 'GLOSA_GRUPO_DIAG2', 'CODIGO_CATEGORIA_DIAG2', 'GLOSA_CATEGORIA_DIAG2', 'CODIGO_SUBCATEGORIA_DIAG2', 'GLOSA_SUBCATEGORIA_DIAG2']
deis = pd.read_csv(deis_csv, sep=';', parse_dates=[1], header=None, names=columnas, index_col=False)
deis.set_index(['FECHA_DEF'], inplace=True)
deis.sort_index(inplace=True)
# CODIGO_CATEGORIA_DIAG1 U07 > covid19 
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
deis['EDAD_ANOS'] = deis.apply(annos, axis = 1)
bins = [0, 20, 30, 40, 50, 60, 70, 80, 999]
labels = ['<=19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '>=80']
deis['agerange'] = pd.cut(deis.EDAD_ANOS, bins, labels=labels, include_lowest=True, right=False)

deis_gruped = pd.pivot_table(deis.loc[(deis['CODIGO_CATEGORIA_DIAG1'] == 'U07')], values=['EDAD_CANT'], index=['FECHA_DEF'],
                    columns=['agerange'], aggfunc='count')['EDAD_CANT']
deis_gruped = deis_gruped.resample('D').asfreq().fillna(0)
deis_gruped.sum()


susceptibles = deis_gruped.copy()
susceptibles['<=19'] = piramide['<=19']
susceptibles['20-29'] = piramide['20-29']
susceptibles['30-39'] = piramide['30-39']
susceptibles['40-49'] = piramide['40-49']
susceptibles['50-59'] = piramide['50-59']
susceptibles['60-69'] = piramide['60-69']
susceptibles['70-79'] = piramide['70-79']
susceptibles['>=80'] = piramide['>=80']

efectividad = 56

susceptibles_timeseries = susceptibles.subtract(casos_m.shift(14).cumsum().fillna(0), fill_value=0).iloc[:-2].subtract(dosis2.shift(14).cumsum().fillna(0), fill_value=0).iloc[:-3].subtract(deis_gruped.cumsum().fillna(0), fill_value=0).iloc[:-2]
susceptibles_timeseries = susceptibles_timeseries.round(0)
susceptibles_efectividad56_timeseries = susceptibles.subtract(casos_m.shift(14).cumsum().fillna(0), fill_value=0).iloc[:-2].subtract((dosis2.shift(14).cumsum().fillna(0)*(1-efectividad/100)), fill_value=0).iloc[:-3].subtract(deis_gruped.cumsum().fillna(0), fill_value=0).iloc[:-2]
susceptibles_efectividad56_timeseries = susceptibles_efectividad56_timeseries.round(0)
susceptibles_efectividad56_timeseries

susceptibles_timeseries.index.name = 'Fecha'
susceptibles_efectividad56_timeseries.index.name = 'Fecha'
colorder = ['<=19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '>=80']
susceptibles_timeseries.columns = colorder
susceptibles_efectividad56_timeseries.columns = colorder
susceptibles_timeseries.to_csv(f'{outputdir}/Susceptibles.csv')
susceptibles_efectividad56_timeseries.to_csv(f'{outputdir}/Susceptibles_efectividad56.csv')

pd.melt(susceptibles_timeseries, ignore_index=False, var_name='Edad', value_name='Susceptibles').to_csv(f'{outputdir}/Susceptibles_std.csv')
pd.melt(susceptibles_efectividad56_timeseries, ignore_index=False, var_name='Edad', value_name='Susceptibles').to_csv(f'{outputdir}/Susceptibles_efectividad56_std.csv')


# os.remove(f'deis_data/{get_csv_deis()}.csv')
# os.remove(f'deis_data/Diccionario de Datos BBDD-COVID19 liberada.xlsx')
# os.remove(f'deis_data/{get_csv_deis()}.zip')
# os.rmdir('deis_data')
rmtree(deis_data)