import plotly.graph_objects as go
import numpy as np
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import re

def adjust_date(date_string, relativemonths = 1, direction = -1):
    """
    Helper function of plot_companies() in this module.
    Not all companies publish financial statements on 12/31.
    Some do so on 1/31.

    Effectively, 12/31 peformance and 1/31 performance line up.
    At least as far as trending is concerned.

    To make company metrics more plottable, this function adjusts all dates
    in statement['statement']['year'] back one month, then extracts the year and
    converts to text. This tends to line up everyone's reporting periods.

    args:
        date_string: string in format %m/%d/%Y (1/31/2020, for example).
        relativemonths: number of months to add or subtract from a date.
        direction: 1 for add, -1 for subtract

    returns:
        adjusted year: String of year after adjustment is made to the date.
    """
    date = dt.strptime(date_string, '%m/%d/%Y')
    newdate = date + (direction * relativedelta(months = relativemonths))
    adjusted_year = str(newdate.year)

    return adjusted_year

def plot_companies(companies_statements, metric, colors = ['blue','orange','green','red']):
    """
    Takes a list of company statements (dicts from company class) and a string
    that corresponds to an item in the dictionaries to plot.

    Pass statement['metrics'] or statement['statement'], for example.

    args:
        companies_statements: a list of company.statement objects from the
        company class. all items should be same statement. (example:
        amd.income_statement, intel.income_statement, etc.)

        metric: string corresponding to a key in the statement dict that houses
        the metric you want to plot. 'rnd_percent' would find the item at
        company.income_statement['metrics']['rnd_percent'].

        colors: list of colors, matched to companies in index order. each
        company plotted will take one of the colors. throws error if list of
        companies is greater than list of colors. default allows for up to
        4 segments. 4 companies to be plotted.

    returns: Plotly fig.
    """
    data = []
    # Identify and gather metric from the company statement dict
    for i, co in enumerate(companies_statements):
        for key in co.keys():
            if key != 'company' and metric in co[key].keys():
                metric_location = key
                co_metric = co[metric_location][metric]

        try:
            test = co_metric
        except:
            print('{} not found in statement. Double check the statement objects in companies_statements argument.'.format(metric))

        x_var = co['statement']['year_adjusted']
        co_name = co['company'] if isinstance(co['company'], str) else ' + '.join(co['company'])

        plot = go.Scatter(
            mode = 'lines+markers',
            line = dict(color = colors[i], width = 4),
            marker = dict(color = 'black', size = 10, symbol = 'line-ns-open'),
            x = x_var[::-1],
            # need to reverse x and y bc default is present - past order
            y = np.flip(co_metric) / 1000000 if metric_location == 'statement' else np.flip(co_metric),
            name = co_name
        )

        data.append(plot)

    layout = dict(
        title = 'Contrasting {}'.format(re.sub('_',' ',metric).upper()),
        plot_bgcolor = 'white',
        height = 400,
        width = 600,
        hovermode = 'x unified',
        xaxis = dict(
            title = 'Year',
            showgrid = False,
            showline = True,
            linecolor = 'black'
            ),
        yaxis = dict(
            title = metric + ' USD (B)' if metric_location == 'statement' else 'Ratio USD',
            showgrid = False,
            showline = True,
            linecolor = 'black',
            tickformat = ',' if metric_location == 'statement' else ',.0' if '_per_' in metric else ',.0%',
            rangemode = 'tozero'
            )
    )

    fig = go.Figure(data = data, layout = layout)

    return fig
