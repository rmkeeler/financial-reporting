import plotly.graph_objects as go
from modules.cleaning import unclean_statement_heading
import numpy as np
import re

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

        TO DO: auto-adjust chart x axis (year_adjusted) for years common to all companies provided

    returns: Plotly fig.
    """
    ## WORK IN PROGRESS:
    # Instantiating a statement_codes dict
    # Eventually will allow a user to provide a list of company objects
    # Rather than a list of company.statement objects
    # Better usability and ability to plot metrics from multiple statements
    statement_codes = {
    'is':None,
    'bs':None,
    'cfs':None
    }

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
