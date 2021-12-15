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

from modules.functions_financials import get_income_statement, get_balance_sheet, get_cash_flow
from modules.functions_filemanagement import save_dictlike

class company():
    """
    Stores a company's three primary financial statements after scraping
    them from yahoo finance.

    Automatically calculates key financial ratios from those documents in
    numpy arrays for easy trending.
    """
    def __init__(self, ticker_symbol, initial_statements=['is','bs','cfs']):
        """
        Just provide a ticker symbol and optionally list the statements with
        which to pop your instance.

        is = income statement
        bs = balance sheet
        cfs = cash flow statement

        In return, the instance will store the statement(s) you wanted as well
        as automatically calculated trends of financial ratios.
        """
        self.ticker = ticker_symbol
        self.contained_statements = initial_statements

        # FINANCIAL STATEMENTS
        self.income_statement_url = 'https://finance.yahoo.com/quote/{}/financials'.format(ticker_symbol)
        self.income_statement, self.income_subrows = get_income_statement(ticker_symbol) if 'is' in initial_statements else (dict(), dict())

        self.balance_sheet_url = 'https://finance.yahoo.com/quote/{}/balance-sheet'.format(ticker_symbol)
        self.balance_sheet, self.balance_subrows = get_balance_sheet(ticker_symbol) if 'bs' in initial_statements else (dict(), dict())

        self.cash_flow_url = 'https://finance.yahoo.com/quote/{}/cash-flow'.format(ticker_symbol)
        self.cash_flow, self.cash_subrows = get_cash_flow(ticker_symbol) if 'cfs' in initial_statements else (dict(), dict())

        # FINANCIAL RATIOS - INCOME
        if 'is' in initial_statements:
            self.gross_margin = self.income_statement['gross_profit'] / self.income_statement['total_revenue']
            self.operating_margin = self.income_statement['operating_income'] / self.income_statement['total_revenue']

            self.sga_percent = self.income_statement['selling_general_and_administrative'] / self.income_statement['total_revenue']
            self.rnd_percent = self.income_statement['research_and_development'] / self.income_statement['total_revenue']

    def save_statements(self, statements = None):
        """
        Save statements stored in the instance to csv file after converting to dataframe.
        """
        if statements == None:
            statements = self.contained_statements

        print('Statements to be saved: {}'.format(statements))
        if 'is' in statements:
            filename = OUTPUT_PATH + self.ticker + '_is.csv'
            save_dictlike(self.income_statement, filename)

        if 'bs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_bs.csv'
            save_dictlike(self.balance_sheet, filename)

        if 'cfs' in statements:
            filename = OUTPUT_PATH + self.ticker + '_cfs.csv'
            save_dictlike(self.cash_flow, filename)

        return None
