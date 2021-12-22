"""
This file contains the classes we'll use to create company objects.

A company object represents one publicly traded company with a page on yahoo finance.

It stores the three major financial statements as dicts.

It automatically calculates ratios insightful for financial statement analysis.

Further analysis can be done on the object's attributes.
"""

from definitions import WEBDRIVER_PATH
from definitions import OUTPUT_PATH
import sys
sys.path.append(WEBDRIVER_PATH) # Selenium breaks if not add to path

from modules.functions_scraping import scrape_statement
from modules.functions_files import save_statement, import_statement
from modules.functions_plotting import adjust_date

import numpy as np
import plotly.graph_objects as go

class company():
    """
    Stores a company's three primary financial statements after scraping
    them from yahoo finance.

    Automatically calculates key financial ratios from those documents in
    numpy arrays for easy trending.
    """
    def __init__(self, ticker_symbol = None, initial_statements=['is','bs','cfs'], method = 'import'):
        """
        Just provide a ticker symbol and optionally list the statements with
        which to pop your instance.

        is = income statement
        bs = balance sheet
        cfs = cash flow statement

        "method" argument tells the class to populate an instance by scraping for the ticker company's
        data or by importing it from the output folder in the project directory.

        In return, the instance will store the statement(s) you wanted as well
        as automatically calculated trends of financial ratios.
        """
        initial_statements = [] if ticker_symbol == None else initial_statements

        self.ticker = ticker_symbol
        self.contained_statements = initial_statements

        # FINANCIAL STATEMENTS
        self.income_statement_url = 'https://finance.yahoo.com/quote/{}/financials'.format(ticker_symbol)
        self.balance_sheet_url = 'https://finance.yahoo.com/quote/{}/balance-sheet'.format(ticker_symbol)
        self.cash_flow_url = 'https://finance.yahoo.com/quote/{}/cash-flow'.format(ticker_symbol)

        if method == 'scrape':
            self.income_statement = scrape_statement(ticker_symbol, 'is') if 'is' in initial_statements else dict()
            self.balance_sheet = scrape_statement(ticker_symbol, 'bs') if 'bs' in initial_statements else dict()
            self.cash_flow = scrape_statement(ticker_symbol, 'cfs') if 'cfs' in initial_statements else dict()
        elif method == 'import':
            self.income_statement = import_statement(OUTPUT_PATH + ticker_symbol + '_is.json') if 'is' in initial_statements else dict()
            self.balance_sheet = import_statement(OUTPUT_PATH + ticker_symbol + '_bs.json') if 'bs' in initial_statements else dict()
            self.cash_flow = import_statement(OUTPUT_PATH + ticker_symbol + '_cfs.json') if 'cfs' in initial_statements else dict()

    def calculate_metrics(self):
        """
        Simply refreshes the metrics stored in the company object's 'metrics' index.

        Pulling it out as a method rather than initializing with these attributes
        because certain methods will add data to the 'statements' indices of statement
        attributes, and this method will allow the object to recalculate its metrics
        after each addition or other update.
        """
        if 'is' in self.contained_statements:
            metrics_is = self.income_statement['statement']
            self.income_statement['metrics'] = dict()
            self.income_statement['metrics']['gross_margin'] = metrics_is['gross_profit'] / metrics_is['total_revenue']
            self.income_statement['metrics']['operating_margin'] = metrics_is['operating_income'] / metrics_is['total_revenue']

            self.income_statement['metrics']['cogs_percent'] = metrics_is['cost_of_revenue'] / metrics_is['total_revenue']
            self.income_statement['metrics']['sga_percent'] = metrics_is['selling_general_and_administrative'] / metrics_is['total_revenue']
            self.income_statement['metrics']['rnd_percent'] = metrics_is['research_and_development'] / metrics_is['total_revenue']
            if 'operating_expense' in self.income_statement['statement'].keys():
                self.income_statement['metrics']['opex_percent'] = metrics_is['operating_expense'] / metrics_is['total_revenue']

        if 'bs' in self.contained_statements:
            metrics_bs = self.balance_sheet['statement']
            self.balance_sheet['metrics'] = dict()
            self.balance_sheet['metrics']['current_ratio'] = metrics_bs['current_assets'] / metrics_bs['current_liabilities']
            self.balance_sheet['metrics']['debt_equity_ratio'] = metrics_bs['total_liabilities_net_minority_interest'] / metrics_bs['total_equity_gross_minority_interest']

        if 'cfs' in self.contained_statements:
            metrics_cfs = self.cash_flow['statement']
            self.cash_flow['metrics'] = dict()
            if 'bs' in self.contained_statements:
                # NOTE: Need to take indices 1: of cash flow arrays, here
                # Balance sheet doesn't have a value for ttm
                # So its arrays will always be 1 shorter than is and cfs arrays
                self.cash_flow['metrics']['operatingcf_ratio'] = metrics_cfs['operating_cash_flow'][1:] / metrics_bs['total_liabilities_net_minority_interest']
            if 'is' in self.contained_statements:
                # NOTE: basic average shares not reported for ttm, so need to take [1:] for both metrics in operatingcf_per_share
                self.cash_flow['metrics']['operatingcf_per_share'] = metrics_cfs['operating_cash_flow'][1:] / metrics_is['basic_average_shares'][1:]

    def save_statements(self, statements = None):
        """
        Save statements stored in the instance to csv file after
        converting to dataframe and long structure.
        """
        if statements == None:
            statements = self.contained_statements

        print('Statements to be saved: {}'.format(statements))
        if 'is' in statements:
            filename = OUTPUT_PATH + self.ticker + '_is.json'
            save_statement(self.income_statement, filename)

        if 'bs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_bs.json'
            save_statement(self.balance_sheet, filename)

        if 'cfs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_cfs.json'
            save_statement(self.cash_flow, filename)

        return None

    def plot_metrics(self, statement, metrics, colors = ['darkblue','orange','lightblue','black','green']):
        """
        Trends one or more metrics for the company to whom the object belongs.

        args:
            statement: string. is, bs or cfs. the statement in the company object
            from which to draw metrics for plotting.

            metrics: list of strings corresponding to keys in the ['statement']
            or ['metrics'] dicts of the given statement.

            colors: list of colors to be applied to series in the plotly trend.
            colors indices correspond to metrics indices.
        """
        statement_codes = {
        'is':self.income_statement,
        'bs':self.balance_sheet,
        'cfs':self.cash_flow
        }

        if statement not in statement_codes.keys():
            raise ValueError('Invalid statement argument. Should be is, bs or cfs. You provided {}'.format(statement))

        statement = statement_codes[statement]

        data = []
        x_var = [adjust_date(x, 1) if x != 'ttm' else x for x in statement['statement']['year']][::-1]
        for i, metric in enumerate(metrics):
            for key in statement.keys():
                if key != 'company' and metric in statement[key].keys():
                    metric_location = key
                    metric_vals = statement[metric_location][metric]

            plot = go.Scatter(
                mode = 'lines+markers',
                line = dict(color = colors[i], width = 4),
                marker = dict(color = 'black', size = 10, symbol = 'line-ns-open'),
                x = x_var,
                y = np.flip(metric_vals) / 1000000 if metric_location == 'statement' else np.flip(metric_vals),
                name = metric
            )

            data.append(plot)

        layout = dict(
            title = 'Contrasting Metrics for {}'.format(statement['company']),
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
                title = 'US Dollars (MM)' if metric_location == 'statement' else 'Ratio USD',
                showgrid = False,
                showline = True,
                linecolor = 'black',
                tickformat = ',.0%' if metric_location == 'metrics' else ','
            )
        )

        fig = go.Figure(data = data, layout = layout)

        return fig
