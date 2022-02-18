from modules.classes import company
import argparse

parser = argparse.ArgumentParser(description = 'Take a stock ticker symbol and gather company financials from Yahoo Finance.')
parser.add_argument('ticker', type = str, help = 'All-caps ticker symbol of a company on Yahoo Finance. Script will gather all three financial statements for that company.')
args = parser.parse_args()


ticker = args.ticker

co = company(ticker, method = 'scrape')

co.save_statements()
