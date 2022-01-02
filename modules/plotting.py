import plotly.graph_objects as go
from modules.cleaning import unclean_statement_heading
import numpy as np
import re

def plot_companies(companies, metric, colors = ['blue','orange','green','red']):
    """
    Takes a list of company statements (dicts from company class) and a string
    that corresponds to an item in the dictionaries to plot.

    Pass statement['metrics'] or statement['statement'], for example.

    args:
        companies: a list of company objects from the
        company class.

        metric: string corresponding to a key in the statement dict that houses
        the metric you want to plot. 'rnd_percent' would find the item at
        company.income_statement['metrics']['rnd_percent'].

        colors: list of colors, matched to companies in index order. each
        company plotted will take one of the colors. throws error if list of
        companies is greater than list of colors. default allows for up to
        4 segments. 4 companies to be plotted.

        TO DO: auto-adjust chart x axis (year_adjusted) for years common to all companies provided

    returns: Plotly fig.
    """
    data = []
    # Identify and gather metric from the company statement dict
    for i, co in enumerate(companies):
        for statement_key in co.statements.keys():
            for data_key in co.statements[statement_key].keys():
                if isinstance(co.statements[statement_key][data_key], dict) and metric in co.statements[statement_key][data_key].keys():
                    metric_location = data_key
                    metric_statement = statement_key
                    co_metric = co.statements[statement_key][data_key][metric]

        try:
            test = co_metric
        except:
            print('{} not found in statement. Double check the statement objects in companies argument.'.format(metric))

        x_var = co.statements[metric_statement]['statement']['year_adjusted']
        co_name = co.statements[metric_statement]['company'] if isinstance(co.statements[metric_statement]['company'], str) else ' + '.join(co.statements[metric_statement]['company'])

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
        title = 'Contrasting {}'.format(unclean_statement_heading(metric)),
        plot_bgcolor = 'white',
        height = 700,
        width = 1050,
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
            tickformat = ',.2',
            rangemode = 'tozero'
            )
    )

    fig = go.Figure(data = data, layout = layout)

    return fig
