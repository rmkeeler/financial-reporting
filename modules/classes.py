"""
This file contains the classes we'll use to create company objects.

A company object represents one publicly traded company with a page on yahoo finance.

It stores the three major financial statements as dicts.

It automatically calculates ratios insightful for financial statement analysis.

Further analysis can be done on the object's attributes.
"""

from definitions import WEBDRIVER_PATH, OUTPUT_PATH, ASSET_PATH
import sys
sys.path.append(WEBDRIVER_PATH) # Selenium breaks if not add to path

from modules.scraping import scrape_statement, get_recent_quarter
from modules.cleaning import unclean_statement_heading, rewrite_value, adjust_date, align_arrays
from modules.forex import trend_mean_rates, get_cpiu
from modules.files import save_json, import_statement_json, import_json

import numpy as np
import pandas as pd
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
        self.currency = '[Unspecified Currency]'

        # point out rows in gathered statements that are calculations rather
        # than simply reported measurements.
        # we'll remove these from statements and recalculate them as metrics
        # this will make it easier to add company instances in reasonable ways
        # with __add__() method
        self.metrics_rows = {'is' : ['Basic EPS','Diluted EPS','Tax Rate for Calcs'],
                                'bs' : ['Working Capital'],
                                'cfs' : []}

        # FINANCIAL STATEMENTS
        self.statement_urls = {'is':'https://finance.yahoo.com/quote/{}/financials'.format(ticker_symbol),
                                'bs':'https://finance.yahoo.com/quote/{}/balance-sheet'.format(ticker_symbol),
                                'cfs':'https://finance.yahoo.com/quote/{}/cash-flow'.format(ticker_symbol)}

        # Instantiate empty dict to hold financial statements
        self.statements = dict()

        if method == 'scrape':
            self.statements['is'] = scrape_statement(ticker_symbol, 'is', skip_rows = self.metrics_rows) if 'is' in initial_statements else dict()
            self.statements['bs'] = scrape_statement(ticker_symbol, 'bs', skip_rows = self.metrics_rows) if 'bs' in initial_statements else dict()
            self.statements['cfs'] = scrape_statement(ticker_symbol, 'cfs', skip_rows = self.metrics_rows) if 'cfs' in initial_statements else dict()
        elif method == 'import':
            self.statements['is'] = import_statement_json(OUTPUT_PATH + ticker_symbol + '_is.json') if 'is' in initial_statements else dict()
            self.statements['bs'] = import_statement_json(OUTPUT_PATH + ticker_symbol + '_bs.json') if 'bs' in initial_statements else dict()
            self.statements['cfs'] = import_statement_json(OUTPUT_PATH + ticker_symbol + '_cfs.json') if 'cfs' in initial_statements else dict()
        else:
            self.statements = dict()

    def align_statements(self):
        """
        In some cases, several statements in a single company object can have assymmetrical
        time frames. This method remedies that, filtering all statements in an
        object for years common to them all.

        This is designed to enable calculate_metrics(), as that method will fail
        for metrics calculated across assymmetrical statements.

        Example: Intel's Cash Flow Statement and Balance Sheet contain different
        time frames. Cash Flow starts at 1989, while Balance Sheet starts at 1985.
        """
        # STEP 1: Figure out which statements are in this object
        statements = {k:v['statement'] for k, v in self.statements.items() if 'statement' in v.keys()}

        # STEP 2: Figure out which years all included statements have in common
        common_years = list(statements.values())[0]['year_adjusted']
        for statement in statements.values():
            common_years = list(set(common_years) & set(statement['year_adjusted']))
            common_years.sort(reverse = True)

        # STEP 3: Run align_arrays() on all statements in statements
        for k, v in statements.items():
            statement_years = v['year_adjusted']
            for row in v:
                v[row] = align_arrays(common_years, statement_years, v[row])
                # STEP 4: Replace the ['statement'] values in each statement in self.statements
                # with the statement in statements dict from step 3
                self.statements[k]['statement'] = statements[k]

        return statements

    def calculate_metrics(self):
        """
        Simply refreshes the metrics stored in the company object's 'metrics' index.

        Pulling it out as a method rather than initializing with these attributes
        because certain methods will add data to the 'statements' indices of statement
        attributes, and this method will allow the object to recalculate its metrics
        after each addition or other update.
        """
        # First, align statements to make sure all the math works
        # Also removes the need to make sure we call this every time we run calcs
        self.align_statements()

        if 'is' in self.statements.keys():
            statement = self.statements['is']
            metrics_is = statement['statement']
            statement['metrics'] = dict()

            statement['metrics']['gross_margin'] = metrics_is['gross_profit'] / metrics_is['total_revenue']
            statement['metrics']['operating_margin'] = metrics_is['operating_income'] / metrics_is['total_revenue']
            statement['metrics']['net_margin'] = metrics_is['net_income'] / metrics_is['total_revenue']

            statement['metrics']['profit_ratio'] = metrics_is['net_income'] / metrics_is['operating_income']

            statement['metrics']['cogs_percent'] = metrics_is['cost_of_revenue'] / metrics_is['total_revenue']

            try:
                statement['metrics']['sga_percent'] = metrics_is['selling_general_and_administrative'] / metrics_is['total_revenue']
            except:
                statement['metrics']['sga_percent'] = np.zeros_like(metrics_is['total_revenue'])

            try:
                statement['metrics']['rnd_percent'] = metrics_is['research_and_development'] / metrics_is['total_revenue']
            except:
                statement['metrics']['rnd_percent'] = np.zeros_like(metrics_is['total_revenue'])
            statement['metrics']['opex_percent'] = metrics_is['operating_expense'] / metrics_is['total_revenue']

            # NOTE: Need to handle divide by zero, here, because items are 0 in ttm column (like basic average shares)
            # Just return 0. In ttm column, shares and eps will both be 0. intuitive to understand that data missing.
            statement['metrics']['tax_rate'] = np.divide(metrics_is['tax_provision'], metrics_is['pretax_income'],
                                                                    out = np.zeros_like(metrics_is['tax_provision']),
                                                                    where = metrics_is['pretax_income'] != 0)
            statement['metrics']['basic_earnings_per_share'] = np.divide(metrics_is['net_income'], metrics_is['basic_average_shares'],
                                                                    out = np.zeros_like(metrics_is['net_income']),
                                                                    where = metrics_is['basic_average_shares'] != 0)
            statement['metrics']['diluted_earnings_per_share'] = np.divide(metrics_is['net_income'], metrics_is['diluted_average_shares'],
                                                                    out = np.zeros_like(metrics_is['net_income']),
                                                                    where = metrics_is['diluted_average_shares'] != 0)

        if 'bs' in self.statements.keys():
            statement = self.statements['bs']
            metrics_bs = statement['statement']
            statement['metrics'] = dict()

            statement['metrics']['current_ratio'] = metrics_bs['current_assets'] / metrics_bs['current_liabilities']
            try:
                statement['metrics']['quick_ratio'] = (metrics_bs['current_assets'] - metrics_bs['inventory']) / metrics_bs['current_liabilities']
            except:
                statement['metrics']['quick_ratio'] = np.zeros_like(metrics_bs['year_adjusted'])
            statement['metrics']['debt_equity_ratio'] = metrics_bs['total_liabilities_net_minority_interest'] / metrics_bs['total_equity_gross_minority_interest']
            statement['metrics']['working_capital'] = metrics_bs['current_assets'] - metrics_bs['current_liabilities']

        if 'cfs' in self.statements.keys():
            statement = self.statements['cfs']
            metrics_cfs = statement['statement']
            statement['metrics'] = dict()

            if 'bs' in self.statements.keys():
                # because we call align_statements() at the beginning of this method,
                # we don't need to do anything to make sure arrays are same size
                statement['metrics']['operating_cf_ratio'] = np.divide(metrics_cfs['operating_cash_flow'], metrics_bs['total_liabilities_net_minority_interest'])

            if 'is' in self.statements.keys():
                # NOTE: basic average shares not reported for ttm, so just fill this metric with 0 for that period
                statement['metrics']['operating_cf_per_share'] = np.divide(metrics_cfs['operating_cash_flow'], metrics_is['basic_average_shares'],
                                                                            out = np.zeros_like(metrics_cfs['operating_cash_flow']),
                                                                            where = metrics_is['basic_average_shares'] != 0)

    def fill_ttm(self, statement, ttm_row):
        """
        Some rows in financial statements are unpopulated in ttm period.
        Basic Average Shares is one of them.
        For some analyses, it's useful and practical to use the value from the
        most recent completed quarter.

        This method does that. Gets most recent completed quarter from Yahoo Finance
        and fills the ttm column in the row specified by fill_row.

        args:
            statement: is, bs or cfs. Which statement to check and to fill.
            fill_row: string. Name of row as it appears on Yahoo Finance. Case sensitive.

        returns: None
        """
        statement_url = self.statement_urls[statement]
        recent_quarter, row_name = get_recent_quarter(statement_url, ttm_row)
        print('Recent Quarter: {}\nRow Name: {}'.format(recent_quarter, row_name))

        # Figure out which index in the provided statement is ttm
        # Return that index, so we can replace the correct index
        # in fill_row with recent_quarter
        ttm_index = self.statements[statement]['year'].index('ttm')
        print('ttm_index: {}'.format(ttm_index))

        self.statements[statement] = rewrite_value(self.statements[statement],row_name,[ttm_index],[recent_quarter])

        return self.statements[statement][row_name]

    def convert_currency(self, currency_a, currency_b):
        """
        When financial statements are in a non-US currency, this method
        converts all statements using a conversion table supplied by the
        developer using this package.

        NOTE: CURRENCY JSON MUST EXIST IN ASSETS FOLDER OF THIS PROJECT'S
        DIRECTORY. Generate such json files with modules.forex.trend_mean_rates()
        and then modules.files.save_json().

        args:
            conversion_array: a 2D numpy array. Shape is years x conversion rate.
            Example: [['2019', 1.5], ['2020', 1.4], ['2021', 1.6]].
            To be matched against ['year_adjusted'] index of financial statements.
        """
        forex_file = ASSET_PATH + currency_a.lower() + '_to_' + currency_b.lower() + '.json'
        forex_rates = import_json(forex_file)
        # STEP 1: Find years in company ['year_adjusted']
        for statement in self.statements.keys():
            statement_dict = self.statements[statement]['statement']

            statement_years = statement_dict['year_adjusted']
            forex_years = forex_rates.keys()

            # STEP 1: Filter forex dict for years in year_adjusted
            filtered_forex = {k:v for (k,v) in forex_rates.items() if k in statement_years}

            # Need to flip forex_factors, because statements store years in reverse order
            # While currency mapping json stores years in chron order
            forex_factors = np.flip(np.asarray(list(filtered_forex.values())))

            # STEP 2: Multiply each row of statement from array created in step 2
            for row in statement_dict.keys():
                # Filter row for only the indices matching year_adjusted in forex_factors
                statement_dict[row] = align_arrays(forex_years, statement_years, statement_dict[row])
                if isinstance(statement_dict[row], np.ndarray):
                    statement_dict[row] = np.rint(statement_dict[row] * forex_factors)

        self.currency = currency_b

        return filtered_forex

    def normalize_statements(self, reference_year = 0, origin_currency = 'USD'):
        """
        Values in Yahoo Finance statements are reported in nominal currency.

        This method converts all values to real values, inflating all years up
        to the most recent year in the financial statement.

        Because CPI package only works in USD, convert_currency() will be run
        when an origin_currency value other than 'USD' is provided.

        args:
            reference_year: default is max year in statement's adjusted_year field.
            Effect is inflating all years up to the current year's dollar value.
            Otherwise, an int year will adjust all values to the year specified,
            as long as that year is actually counted in the statements analyzed.

            origin_currency: default assumes the statement's currency is USD. No
            forex transformations will be performed on the statements before normalizing.
            String currency code will run convert_currency() method to convert from
            the specified currency to USD before normalizing for inflation. This
            conversion is necessary, because CPI-U is measured on US goods and
            therefore isn't a very insightful measure of inflation in other countries.
            Forex transformation analytically accounts for non-US inflation by tracking
            differences in conversion rate year to year between USD and other currency.
        """
        # If origin_currency is not USD, convert to USD from origin_currency
        # consumer price index is inflation measure based on US prices
        # Imperfect way to do this, but for basic decision making, we can
        # pretend foreign companies are US-based.
        # Foreign currency inflation relative to USD is captured in forex, so
        # this does make international contrasts more insightful
        if origin_currency != 'USD':
            self.convert_currency(origin_currency, 'USD')

        # Figure out which statements are in here
        statements = {k:v['statement'] for k, v in self.statements.items() if 'statement' in v.keys()}
        # Get consumer price index (CPI-U) lookup dict
        cpiu = get_cpiu()
        # Iterate through statements
        for k, v in statements.items():
            # Find max year
            ref_year = str(reference_year) if reference_year and (str(reference_year) in v['year_adjusted']) else max(v['year_adjusted'])
            all_years = v['year_adjusted']
            cpiu_factors = np.asarray([1 + ((cpiu[ref_year] - cpiu[x]) / cpiu[x]) for x in all_years])
            # Get a np array of cpiu factors ((max - current) / current)
            # Iterate through rows
            for i, row in v.items():
                if isinstance(row, np.ndarray):
                    # Adjust whole row with cpiu_factors
                    v[i] = v[i] * cpiu_factors

            # Replace statements.[statement]['statement'] with statement
            self.statements[k]['statement'] = statements[k]

        return None

    def quick_gather(self, ticker):
        """
        Convenience method that scrapes Yahoo Finance for statements for ticker
        company and then saves them with save_statements() in one line.

        Returns the populated company object after gathering.
        """
        co = company(ticker, method = 'scrape')
        co.save_statements()

        return co

    def save_statements(self, statements = None):
        """
        Save statements stored in the instance to csv file after
        converting to dataframe and long structure.
        """
        if statements == None:
            statements = self.statements.keys()

        print('Statements to be saved: {}'.format(statements))
        if 'is' in statements:
            filename = OUTPUT_PATH + self.ticker + '_is.json'
            save_json(self.statements['is'], filename)

        if 'bs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_bs.json'
            save_json(self.statements['bs'], filename)

        if 'cfs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_cfs.json'
            save_json(self.statements['cfs'], filename)

        return None

    def plot(self, metrics, colors = ['darkblue','orange','lightblue','black','green']):
        """
        Trends one or more metrics for the company to whom the object belongs.

        args:
            statement: list. is, bs or cfs. the statement(s) in the company object
            from which to draw metrics for plotting.

            metrics: list of strings corresponding to keys in the ['statement']
            or ['metrics'] dicts of the given statement.

            colors: list of colors to be applied to series in the plotly trend.
            colors indices correspond to metrics indices.
        """
        data = []

        for i, metric in enumerate(metrics):
            for statement_key in self.statements.keys():
                for data_key in self.statements[statement_key].keys():
                    if isinstance(self.statements[statement_key][data_key], dict) and metric in self.statements[statement_key][data_key].keys():
                        metric_location = data_key
                        metric_statement = statement_key
                        metric_vals = self.statements[statement_key][data_key][metric]

            x_var = self.statements[statement_key]['statement']['year_adjusted'][::-1]

            plot = go.Scatter(
                mode = 'lines+markers',
                line = dict(color = colors[i], width = 4),
                marker = dict(color = 'black', size = 10, symbol = 'line-ns-open'),
                x = x_var,
                y = np.flip(metric_vals) / 1000000 if metric_location == 'statement' else np.flip(metric_vals),
                name = metric
            )

            data.append(plot)

        pretty_metrics = [unclean_statement_heading(x) for x in metrics]

        layout = dict(
            title = 'Contrasting {} for {}'.format(', '.join(pretty_metrics), self.ticker),
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
                title = self.currency + ' (B)' if metric_location == 'statement' else 'Ratio ' + self.currency,
                showgrid = False,
                showline = True,
                linecolor = 'black',
                tickformat = ',.6',
                rangemode = 'tozero'
            )
        )

        fig = go.Figure(data = data, layout = layout)

        return fig

    def __repr__(self):
        """
        Calling a company object without an attribute or method will
        display the object's metadata.
        """

        header = '|||Object Metadata|||\n'.format(self.ticker)
        data = [['Companies Included', '{}'.format(', '.join(self.ticker))],
                ['Statements Available', '{}'.format(', '.join(self.statements.keys()))]]

        return header + str(pd.DataFrame(data = [x[1] for x in data], index = [x[0] for x in data], columns = ['']))

    def __add__(self, other):
        """
        Adding instances of this class will add the statements together.

        Returns a new instance of the combined statements. Metrics can be
        recalculated at this combined level on the new instance.

        Imagined use case is combining several companies into a market or a
        segment of companies. Individual company instances can then be
        contrasted with this segment instance.
        """
        # Figure out which statements each object has.
        self_statements = {
        'is':self.statements['is']['statement'] if 'is' in self.statements.keys() else 'Unavailable',
        'bs':self.statements['bs']['statement'] if 'bs' in self.statements.keys() else 'Unavailable',
        'cfs':self.statements['cfs']['statement'] if 'cfs' in self.statements.keys() else 'Unavailable'
        }

        other_statements = {
        'is':other.statements['is']['statement'] if 'is' in other.statements.keys() else 'Unavailable',
        'bs':other.statements['bs']['statement'] if 'bs' in other.statements.keys() else 'Unavailable',
        'cfs':other.statements['cfs']['statement'] if 'cfs' in other.statements.keys() else 'Unavailable'
        }

        # Instantiate a dict that will hold combined statements.
        segment_dict = dict()

        # Instantiate empty entry in segment dict for each statement
        # Ticker and company values in new object will be a list of companies in the new segment
        # Make sure both ticker attributes are lists before attempting to combine them.
        self_ticker = self.ticker if isinstance(self.ticker, list) else [self.ticker]
        other_ticker = other.ticker if isinstance(other.ticker, list) else [other.ticker]
        segment_tickers = self_ticker + other_ticker

        segment_dict['is'] = dict(company = segment_tickers, groupings = dict(), statement = dict())
        segment_dict['bs'] = dict(company = segment_tickers, groupings = dict(), statement = dict())
        segment_dict['cfs'] = dict(company = segment_tickers, groupings = dict(), statement = dict())

        # Only attempt to add statements if both objects have the statement
        for sheet in self.statements.keys():
            if isinstance(self_statements[sheet], dict) and isinstance(other_statements[sheet], dict):
                # Get indices of years in each object that are common to the other object
                # These will be used to filter statement and metrics rows, later
                # To make sure that the whole resulting object only describes years common to both instances.
                years_self = self_statements[sheet]['year_adjusted']
                years_other = other_statements[sheet]['year_adjusted']

                for key in other_statements[sheet]:
                    # Need to handle year in a special way
                    # Only keep years in segment_dict that exist in both component dicts
                    # This avoids the hassle of wondering how many components are
                    # rep'd in each year during analyses
                    if key in ['year_adjusted'] and key in self_statements[sheet]:
                        segment_dict[sheet]['statement'][key] = align_arrays(years_other, years_self, self_statements[sheet][key])
                    elif key not in ['year', 'year_adjusted'] and key in self_statements[sheet]:
                        # indexing for common_years_self and other_years_self makes sure
                        # values in statement rows align with years in year_adjusted
                        self_aligned = align_arrays(years_other, years_self, self_statements[sheet][key])
                        other_aligned = align_arrays(years_self, years_other, other_statements[sheet][key])
                        segment_dict[sheet]['statement'][key] = self_aligned + other_aligned

        # instantiate new company object for the combined segment
        segment = company(ticker_symbol = segment_tickers, method = None)
        segment.ticker = segment_tickers

        segment.statements['is'] = segment_dict['is']
        segment.statements['bs'] = segment_dict['bs']
        segment.statements['cfs'] = segment_dict['cfs']

        segment.metrics_rows = self.metrics_rows

        return segment
