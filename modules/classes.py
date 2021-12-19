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
