from pathlib import Path


import pandas as pd
import numpy as np
import urllib.request
from zipfile import ZipFile
from re import compile
from pathlib import Path
from shutil import rmtree
import calendar
import os
import aesara.tensor as at
import arviz as az
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import seaborn as sns
import xarray as xr
import matplotlib
import datetime
import imageio


def get_deis_death_url():
    datapattern = compile('http.*DEFUNCIONES_FUENTE_DEIS_2016_.*zip\"\\n\"tags\":\"defunciones\"')
    with urllib.request.urlopen('https://deis.minsal.cl/wp-admin/admin-ajax.php?action=wp_ajax_ninja_tables_public_action&table_id=2889&target_action=get-all-data&default_sorting=manual_sort') as f:
        return datapattern.search(f.read().decode().replace(',','\n')).group().replace('\\', '').split('"')[0]

def get_csv_deis():
    url = get_deis_death_url()
    urllib.request.urlretrieve(url, 'deis_data/' + url.split('/')[-1])
    with ZipFile('deis_data/' + url.split('/')[-1], 'r') as zip_ref:
        zip_ref.extractall('deis_data')
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


def ZeroSumNormal(name, *, sigma=None, active_dims=None, dims, model=None):
    model = pm.modelcontext(model=model)

    if isinstance(dims, str):
        dims = [dims]

    if isinstance(active_dims, str):
        active_dims = [active_dims]

    if active_dims is None:
        active_dims = dims[-1]

    def extend_axis(value, axis):
        n_out = value.shape[axis] + 1
        sum_vals = value.sum(axis, keepdims=True)
        norm = sum_vals / (at.sqrt(n_out) + n_out)
        fill_val = norm - sum_vals / at.sqrt(n_out)
        out = at.concatenate([value, fill_val], axis=axis)
        return out - norm

    dims_reduced = []
    active_axes = []
    for i, dim in enumerate(dims):
        if dim in active_dims:
            active_axes.append(i)
            dim_name = f"{dim}_reduced"
            if name not in model.coords:
                model.add_coord(dim_name, length=len(model.coords[dim]) - 1, mutable=False)
            dims_reduced.append(dim_name)
        else:
            dims_reduced.append(dim)

    raw = pm.Normal(f"{name}_raw", sigma=sigma, dims=dims_reduced)
    for axis in active_axes:
        raw = extend_axis(raw, axis)
    return pm.Deterministic(name, raw, dims=dims)


def format_x_axis(ax, minor=False):
    # major ticks
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y %b"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.grid(which="major", linestyle="-", axis="x")
    # minor ticks
    if minor:
        ax.xaxis.set_minor_formatter(mdates.DateFormatter("%Y %b"))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.grid(which="minor", linestyle=":", axis="x")
    # rotate labels
    for label in ax.get_xticklabels(which="both"):
        label.set(rotation=70, horizontalalignment="right")


def plot_xY(x, Y, ax, col='C1', label='Forecast'):
    quantiles = Y.quantile((0.025, 0.25, 0.5, 0.75, 0.975), dim=("chain", "draw")).transpose()

    az.plot_hdi(
        x,
        hdi_data=quantiles.sel(quantile=[0.025, 0.975]),
        fill_kwargs={"alpha": 0.25},
        smooth=False,
        ax=ax,
    )
    az.plot_hdi(
        x,
        hdi_data=quantiles.sel(quantile=[0.25, 0.75]),
        fill_kwargs={"alpha": 0.5},
        smooth=False,
        ax=ax,
    )
    ax.plot(x, quantiles.sel(quantile=0.5), color=col, lw=3, label=label,)

def plot_xY95(x, Y, ax, col='C1', label='Forecast'):
    quantiles = Y.quantile((0.05, 0.5, 0.95), dim=("chain", "draw")).transpose()

    az.plot_hdi(
        x,
        hdi_data=quantiles.sel(quantile=[0.05, 0.95]),
        fill_kwargs={"alpha": 0.5},
        smooth=False,
        ax=ax,
    )
    ax.plot(x, quantiles.sel(quantile=0.5), color=col, label=label,)

if __name__ == "__main__":
    repo_dir = Path(__file__).parent.parent
    outputdir = repo_dir/'output'
    outputdir.mkdir(parents=True, exist_ok=True)
    deis_data = Path('deis_data')
    deis_data.mkdir(parents=True, exist_ok=True)
    deis_csv = 'deis_data/' + get_csv_deis() + 'csv'
    columnas = ['ANO_DEF', 'FECHA_DEF', 'GLOSA_SEXO', 'EDAD_TIPO', 'EDAD_CANT', 'CODIGO_COMUNA_RESIDENCIA', 'GLOSA_COMUNA_RESIDENCIA', 'GLOSA_REG_RES', 'DIAG1', 'CAPITULO_DIAG1', 'GLOSA_CAPITULO_DIAG1', 'CODIGO_GRUPO_DIAG1', 'GLOSA_GRUPO_DIAG1', 'CODIGO_CATEGORIA_DIAG1', 'GLOSA_CATEGORIA_DIAG1', 'CODIGO_SUBCATEGORIA_DIAG1', 'GLOSA_SUBCATEGORIA_DIAG1', 'DIAG2', 'CAPITULO_DIAG2', 'GLOSA_CAPITULO_DIAG2', 'CODIGO_GRUPO_DIAG2', 'GLOSA_GRUPO_DIAG2', 'CODIGO_CATEGORIA_DIAG2', 'GLOSA_CATEGORIA_DIAG2', 'CODIGO_SUBCATEGORIA_DIAG2', 'GLOSA_SUBCATEGORIA_DIAG2']
    deis = pd.read_csv(deis_csv, sep=';', parse_dates=[1], header=None, names=columnas, index_col=False, encoding='latin-1')
    deis.set_index(['FECHA_DEF'], inplace=True)
    deis.sort_index(inplace=True)
    # CODIGO_CATEGORIA_DIAG1 U07 > covid19
    rmtree(deis_data)
    deis['EDAD_ANOS'] = deis.apply(annos, axis = 1)
    deis['ANO_DEF'] = deis['ANO_DEF'].astype('int32')
    bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 999]
    bins_10s = [0, 10, 20, 30, 40, 50, 60, 70, 80, 999]
    labels = ['00-04', '05-09', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', '80+']
    labels_10s = ['00-09', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
    deis['agerange'] = pd.cut(deis.EDAD_ANOS, bins, labels=labels, include_lowest=True, right=False)
    deis['agerange_10s'] = pd.cut(deis.EDAD_ANOS, bins_10s, labels=labels_10s, include_lowest=True, right=False)

    # default figure sizes
    figsize = (10, 5)

    # create a list of month strings, for plotting purposes
    month_strings = calendar.month_name[1:]

    deis_gruped = pd.pivot_table(deis, values=['EDAD_CANT'], index=['FECHA_DEF'],
                        columns=['GLOSA_SEXO', 'agerange_10s'], aggfunc='count')['EDAD_CANT'].resample('W-Mon').sum()
    deis_prepandemia = pd.pivot_table(deis.loc[(deis['ANO_DEF'] <= 2019)], values=['EDAD_CANT'], index=['FECHA_DEF'],
                        columns=['GLOSA_SEXO', 'agerange_10s'], aggfunc='count')['EDAD_CANT'].resample('W-Mon').sum()
    deis_gruped = deis_gruped.sum(axis=1).iloc[1:-2]#.groupby(pd.Grouper(freq='W')).sum().iloc[1:-1]
    deis_prepandemia = deis_prepandemia.sum(axis=1).iloc[1:-1]#.groupby(pd.Grouper(freq='W')).sum().iloc[1:-1]

    sns.set(rc={'figure.figsize':(11.7,8.27)})



    ## MODEL
    with pm.Model(coords={"month": month_strings}) as model:

        # observed predictors and outcome
        month = pm.MutableData("month", deis_prepandemia.index.month.to_numpy(), dims='t')
        time = pm.MutableData("time", np.array(list(range(len(deis_prepandemia)))), dims='t')
        deaths = pm.MutableData("deaths", deis_prepandemia.to_numpy(), dims='t')
        # priors
        intercept = pm.Normal("intercept", 2200, 10)
        month_mu = ZeroSumNormal("month mu", sigma=200, dims="month")
        linear_trend = pm.TruncatedNormal("linear trend", 0, 0.1, lower=0)

        # the actual linear model
        mu = pm.Deterministic(
            "mu",
            intercept + (linear_trend * time) + month_mu[month - 1],
        )
        sigma = pm.HalfNormal("sigma", 1)
        # likelihood
        pm.TruncatedNormal("obs", mu=mu, sigma=sigma, lower=0, observed=deaths, dims='t')


    with model:
        idata = pm.sample(2000,tune=10000, random_seed=42)

    with model:
        pm.set_data(
            {
                "month": deis_gruped.index.month.to_numpy(),
                "time": np.array(list(range(len(deis_gruped)))),
            }
        )
        completecounterfactual = pm.sample_posterior_predictive(
            idata, var_names=["obs"], random_seed=42
        )

    humanweek = deis_gruped.shift(-7, freq='D')

    TITULO = "Exceso de mortalidad para todos los grupos etarios. Chile"

    sns.set_context('paper', font_scale=1.5)

    fig, ax = plt.subplots(3, 1, figsize=(figsize[0]+5, 9), sharex=True, gridspec_kw={'height_ratios': [5, 2, 2]})
    #az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.5, smooth=True)
    az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.95, smooth=False, smooth_kwargs={'window_length':11}, fill_kwargs={"label": "Modelo (95% Confianza)"}, color="C2", ax = ax[0])

    ax[0].plot(humanweek.index, humanweek, label="Defunciones")
    #format_x_axis(ax)
    ax[0].set(title=TITULO)
    ax[0].legend()
    ax[0].set_ylim(ymin=0)
    ax[0].set_ylabel('Defunciones semanales')

    # convert deaths into an XArray object with a labelled dimension to help in the next step
    deaths = xr.DataArray(humanweek.to_numpy(), dims=["t"])

    # do the calculation by taking the difference
    excess_deaths = deaths - completecounterfactual.posterior_predictive["obs"]
    cumsum = excess_deaths.cumsum(dim="t")

    thm = cumsum.transpose(..., "t").quantile((0.05,0.5,0.95), dim=("chain", "draw")).transpose()[-1].to_numpy()
    thm2 = excess_deaths.transpose(..., "t").quantile((0.05,0.5,0.95), dim=("chain", "draw")).transpose()[-1].to_numpy()
    NOTAS = [
        f"Fuente deis.minsal.cl ({deis.index[-1].strftime('%d/%m/%Y')}); Ultima semana analizada {humanweek.index[-1].strftime('%d/%m/%Y')} — {humanweek.shift(7, freq='D').index[-1].strftime('%d/%m/%Y')}; Exceso semanal = {thm2[1]:,.0f} ({thm2[0]:,.0f} — {thm2[2]:,.0f}); Exceso total = {thm[1]:,.0f} ({thm[0]:,.0f} — {thm[2]:,.0f})",
    ]
    enTITULO = "Excess mortality for all age groups. Chile"

    plot_xY95(humanweek.index, excess_deaths.transpose(..., "t"), ax[1], label='Exceso de defunciones')

    ax[1].axhline(y=0, color="k")
    ax[1].legend()
    ax[1].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, cumsum.transpose(..., "t"), ax[2], label='Exceso de defunciones acumulado')
    ax[2].axhline(y=0, color="k")
    ax[2].legend()
    ax[2].set_ylabel('Defunciones')
    ax[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[2].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))


    plt.figtext(0.5, -0.01, NOTAS[0], ha="center", bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})
    ax[0].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))
    ax[1].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))
    ax[2].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))


    img = imageio.v2.imread('https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png')

    # put a new axes where you want the image to appear
    # (x, y, width, height)
    imax = fig.add_axes([0.40, 0.9, 0.25, 0.25])
    # remove ticks & the box from imax 
    imax.set_axis_off()
    # print the logo with aspect="equal" to avoid distorting the logo
    imax.imshow(img, aspect="equal")

    plt.tight_layout()
    #plt.savefig(f'{outputdir}/Defunciones_en_exceso.png', bbox_inches='tight', dpi=300)
    plt.savefig(f'{outputdir}/Defunciones_en_exceso.pdf', bbox_inches='tight', dpi=300)


    fig, ax = plt.subplots(3, 1, figsize=(figsize[0]+5, 9), sharex=True, gridspec_kw={'height_ratios': [5, 2, 2]})
    #az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.5, smooth=True)
    az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.95, smooth=True, smooth_kwargs={'window_length':11}, fill_kwargs={"label": "Modelo (95% Confianza)"}, color="C2", ax = ax[0])

    ax[0].plot(humanweek.index, humanweek, label="Defunciones")
    #format_x_axis(ax)
    ax[0].set(title=TITULO)
    ax[0].legend()
    ax[0].set_ylim(ymin=0)
    ax[0].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, excess_deaths.transpose(..., "t"), ax[1], label='Exceso de defunciones')

    ax[1].axhline(y=0, color="k")
    ax[1].legend()
    ax[1].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, cumsum.transpose(..., "t"), ax[2], label='Exceso de defunciones acumulado')
    ax[2].axhline(y=0, color="k")
    ax[2].legend()
    ax[2].set_ylabel('Defunciones')
    ax[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[2].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))


    plt.figtext(0.5, -0.01, NOTAS[0], ha="center", bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})
    ax[0].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))
    ax[1].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))
    ax[2].set_xlim(xmin=datetime.datetime(2016, 1, 1, ))

    img = imageio.v2.imread('https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png')

    # put a new axes where you want the image to appear
    # (x, y, width, height)
    imax = fig.add_axes([0.40, 0.9, 0.25, 0.25])
    # remove ticks & the box from imax 
    imax.set_axis_off()
    # print the logo with aspect="equal" to avoid distorting the logo
    imax.imshow(img, aspect="equal")

    plt.tight_layout()
    #plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH.png', bbox_inches='tight', dpi=300)
    plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH.pdf', bbox_inches='tight', dpi=300)



    fig, ax = plt.subplots(3, 1, figsize=(figsize[0]+5, 9), sharex=True, gridspec_kw={'height_ratios': [5, 2, 2]})
    #az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.5, smooth=True)
    az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.95, smooth=True, smooth_kwargs={'window_length':11}, fill_kwargs={"label": "Modelo (95% Confianza)"}, color="C2", ax = ax[0])

    ax[0].plot(humanweek.index, humanweek, label="Defunciones")
    #format_x_axis(ax)
    ax[0].set(title=TITULO)
    ax[0].legend()
    ax[0].set_ylim(ymin=0)
    ax[0].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, excess_deaths.transpose(..., "t"), ax[1], label='Exceso de defunciones')

    ax[1].axhline(y=0, color="k")
    ax[1].legend()
    ax[1].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, cumsum.transpose(..., "t"), ax[2], label='Exceso de defunciones acumulado')
    ax[2].axhline(y=0, color="k")
    ax[2].legend()
    ax[2].set_ylabel('Defunciones')
    ax[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[2].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    plt.figtext(0.5, -0.01, NOTAS[0], ha="center", bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})
    ax[0].set_xlim(xmin=datetime.datetime(2020, 1, 1, ))
    ax[1].set_xlim(xmin=datetime.datetime(2020, 1, 1, ))
    ax[2].set_xlim(xmin=datetime.datetime(2020, 1, 1, ))


    img = imageio.v2.imread('https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png')

    # put a new axes where you want the image to appear
    # (x, y, width, height)
    imax = fig.add_axes([0.40, 0.9, 0.25, 0.25])
    # remove ticks & the box from imax 
    imax.set_axis_off()
    # print the logo with aspect="equal" to avoid distorting the logo
    imax.imshow(img, aspect="equal")

    plt.tight_layout()
    #plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH_starton2020.png', bbox_inches='tight', dpi=300)
    plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH_starton2020.pdf', bbox_inches='tight', dpi=300)

    fig, ax = plt.subplots(3, 1, figsize=(figsize[0]+5, 9), sharex=True, gridspec_kw={'height_ratios': [5, 2, 2]})
    #az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.5, smooth=True)
    az.plot_hdi(mdates.date2num(humanweek.index), completecounterfactual.posterior_predictive["obs"], hdi_prob=0.95, smooth=True, smooth_kwargs={'window_length':11}, fill_kwargs={"label": "Modelo (95% Confianza)"}, color="C2", ax = ax[0])

    ax[0].plot(humanweek.index, humanweek, label="Defunciones")
    #format_x_axis(ax)
    ax[0].set(title=TITULO)
    ax[0].legend()
    ax[0].set_ylim(ymin=0)
    ax[0].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, excess_deaths.transpose(..., "t"), ax[1], label='Exceso de defunciones')

    ax[1].axhline(y=0, color="k")
    ax[1].legend()
    ax[1].set_ylabel('Defunciones semanales')

    plot_xY95(humanweek.index, cumsum.transpose(..., "t"), ax[2], label='Exceso de defunciones acumulado')
    ax[2].axhline(y=0, color="k")
    ax[2].legend()
    ax[2].set_ylabel('Defunciones')
    ax[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax[2].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    plt.figtext(0.5, -0.01, NOTAS[0], ha="center", bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})
    ax[0].set_xlim(xmin=datetime.datetime(2022, 1, 1, ))
    ax[1].set_xlim(xmin=datetime.datetime(2022, 1, 1, ))
    ax[2].set_xlim(xmin=datetime.datetime(2022, 1, 1, ))


    img = imageio.v2.imread('https://i2.wp.com/dlab.cl/wp-content/uploads/2016/08/LogoWebDlab.png')

    # put a new axes where you want the image to appear
    # (x, y, width, height)
    imax = fig.add_axes([0.40, 0.9, 0.25, 0.25])
    # remove ticks & the box from imax 
    imax.set_axis_off()
    # print the logo with aspect="equal" to avoid distorting the logo
    imax.imshow(img, aspect="equal")

    plt.tight_layout()
    #plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH_starton2022.png', bbox_inches='tight', dpi=300)
    plt.savefig(f'{outputdir}/Defunciones_en_exceso_SMOOTH_starton2022.pdf', bbox_inches='tight', dpi=300)

