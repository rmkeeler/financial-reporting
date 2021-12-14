from definitions import WEBDRIVER_PATH

# Analysis packages
import numpy as np
import statistics as stat

# Text parsing packages
import re

# Web crawling packages
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# DEFINE FUNCTIONS
def clean_numeric(text, frmat = float):
    """
    Text numbers in text format. Cleans out characters that make conversion to int or float impossible.

    Returns the values in chosen frmat function (i.e. int or float)
    """
    clean_text = text

    # Define replacements
    rep = {',':'',
          '^\-$':'0'}

    for found, replaced in rep.items():
        clean_text = re.sub(found, replaced, clean_text)

    return frmat(clean_text)

def create_webdriver():
    """
    Create and return a Chrome web driver for use in this app's scraping functions.

    We're using a webdriver instead of just raw requests, because yahoo finance income statement rows
    sometimes need to be expanded with an HTML button (like OpEx).
    """
    # Specify the file of the driver to be used
    driver_name = 'chromedriver.exe'

    # Instantiate driver options
    options = webdriver.ChromeOptions()

    # Specify driver options
    options.add_argument('--headless')
    options.add_argument('--ignore_certificate_errors')
    options.add_argument('--incognito')

    # Instantiate driver service
    service = Service(WEBDRIVER_PATH + driver_name)

    # Instantiate driver
    driver = webdriver.Chrome(service = service, options = options)

    return driver

def get_income_rows(webdriver, ticker_symbol):
    """
    Get income statement for company = ticker_symbol from yahoo finance.

    Only returns the set of divs on the page corresponding to income statement rows and its header.

    Recommended use case is passing the output to the following dictify_income() function to get a proper
    income statement dict with many more use cases.
    """
    url = 'https://finance.yahoo.com/quote/{}/financials'.format(ticker_symbol)
    # Open the page in webdriver
    webdriver.get(url)

    # Expand the OpEx row on the page
    webdriver.find_element(By.XPATH, '//button[@aria-label="Operating Expense"]').click()

    # Get the page's soup
    soup = BeautifulSoup(webdriver.page_source, 'lxml')

    # Get the income statement's heading
    statement_heading = soup.find('div',{'class':'D(tbhg)'}).select_one('div:first-child').find_all('div')

    # Get list of divs from the page source that correspond to income statement rows
    statement_rows = soup.find_all('div',{'data-test':'fin-row'})

    return statement_heading, statement_rows

def dictify_income(statement_heading, statement_rows):
    """
    Takes an income statement heading and a list of income statement rows as returned by get_income_statement().
    Literally, these are sets of divs from the yahoo finance page's dom.

    Gets rid of all the dom baggage and returns a simple dict of income statement rows.
    """
    # Instantiate the income_dict
    income_dict = dict()

    ## STEP 1: Get the years column before doing anything else. Requires special process.
    # We take indices [2:], because first two columns are the row name ("breakdown") and a blank column for formatting
    income_dict['Year'] = np.array([x.text for x in statement_heading[2:]])

    ## STEP 2.PREAMBLE: Establish the mode number of columns in the income statement
    # We'll use this to weed out subheader rows that have been expanded (subheader rows will show more columns than mode value)
    # Requires statistics package aliased as "stat"
    col_counts = list()
    for row in statement_rows:
        col_counts.append(len(row.find_all('div',{'data-test':'fin-col'})))
    col_mode = stat.mode(col_counts)

    ## STEP 2: Iterate through income statement rows and pull out the values into the dict
    for row in statement_rows:
        # Get a list of the columns in the row
        cols = row.find_all('div',{'data-test':'fin-col'})

        # Check to see if column count == the col_mode we calculated above
        # If yes, it's safe for extraction into the dict
        # If no, it's an expanded subheader row, and we should skip it
        # Result is several rows for the components of OpEx and NO separate row for the OpEx aggregate
        if len(cols) == col_mode:

            # Light cleaning: get rid of commas, replace '-' with zero, format all values as floats rather than text
            rowvals = np.array([clean_numeric(x.text) for x in cols])
            rowname = row.select_one('div:first-child').find_all('div')[0].text

            income_dict[rowname] = rowvals

    return income_dict

def get_income_statement(ticker):
    """
    Run all necessary functions above to get an income statement dict at once.
    """
    driver = create_webdriver()
    income_heading, income_rows = get_income_rows(driver, ticker)
    income_dict = dictify_income(income_heading, income_rows)
    return income_dict
