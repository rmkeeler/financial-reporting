import plotly.graph_objects as go
from modules.cleaning import unclean_statement_heading
import numpy as np
import re

def plot_companies(companies, metric, colors = ['blue','orange','green','red','black','purple']):
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
    # Choose currency of first company provided for use in plot labeling.
    currency = companies[0].currency
    print('Using reporting currency of {}: {}'.format(companies[0].ticker, currency))

    data = []
    # Identify and gather metric from the company statement dict
    for i, co in enumerate(companies):
        # Look through each statement for the metric
        for statement_key in co.statements.keys():
            # Look through each value in the statement dict for the one that contains the metric specified
            for data_key in co.statements[statement_key].keys():
                # Get data from the value that contains the metric as a key.
                # Skip the value if it's not a dict (statement values are aleays in a dict)
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
            linecolor = 'black',
            # When companies have asymmetrical time frames, plotting them in random
            # order can cause the series with the earliest year to put its earliest year
            # at the end of the x axis scale. counter this with categoryorder below.
            categoryorder = 'category ascending'
            ),
        yaxis = dict(
            title = metric + ' ' + currency + ' (B)' if metric_location == 'statement' else currency + ' USD',
            showgrid = False,
            showline = True,
            linecolor = 'black',
            tickformat = ',.6',
            rangemode = 'tozero'
            )
    )

    fig = go.Figure(data = data, layout = layout)

    return fig
