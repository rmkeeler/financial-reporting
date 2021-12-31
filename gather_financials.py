from modules.classes import company

ticker = input('Which company to gather? (Ticker Symbol)')

co = company(ticker, method = 'scrape')

co.save_statements()
