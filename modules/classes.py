"""
This file contains the classes we'll use to create company objects.

A company object represents one publicly traded company with a page on yahoo finance.

It stores the three major financial statements as dicts.

It automatically calculates ratios insightful for financial statement analysis.

Further analysis can be done on the object's attributes.
"""

from definitions import WEBDRIVER_PATH
import sys
sys.path.append(WEBDRIVER_PATH) # Selenium breaks if not add to path

from modules.functions_income import get_income_statement

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

        # FINANCIAL STATEMENTS
        self.income_statement_url = 'https://finance.yahoo.com/quote/{}/financials'.format(ticker_symbol)
        self.income_statement, self.income_subrows = get_income_statement(ticker_symbol) if 'is' in initial_statements else dict()

        self.balance_sheet_url = 'https://finance.yahoo.com/quote/{}/balance-sheet'.format(ticker_symbol)
        self.balance_sheet = dict()

        self.cash_flow_url = 'https://finance.yahoo.com/quote/{}/cash-flow'.format(ticker_symbol)
        self.cash_flow = dict()

        # FINANCIAL RATIOS
        self.gross_margin = self.income_statement['Gross Profit'] / self.income_statement['Total Revenue']
        self.operating_margin = self.income_statement['Operating Income'] / self.income_statement['Total Revenue']
