from definitions import WEBDRIVER_PATH
from time import sleep

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

def clean_statement_heading(heading):
    """
    Helper function of dictify_statement(). Cleans out normal garbage from
    table heading strings.
    """
    clean_heading = re.sub(' ','_',heading).replace('&','and').lower()

    return clean_heading

def extract_row_name(row_text):
    """
    Method I'm using to grab yahoo finance statement rows produces at one point
    lines of text that concatenate a row name with the values in all of the row's
    columns.

    Example: Current Assets47,249,00031,239,00028,787,00029,500,000

    This function cleans that up and returns just the row name (Current Assets).
    Also cleans the names using clean_statement_heading so they're ready to be
    added to a statement's dictionary.
    """
    step_one = re.sub('[0-9]+','|',re.sub(',','',row_text)).rsplit('|',1)[0].split('|')[1:]
    # yahoo fin statements use '-' instead of zero
    # gets confusing when a row's name is hyphenated
    # need this second step to process hyphens in the right way
    step_two = [x.strip('-') for x in step_one if re.search('[^\-]+',x)]

    return step_two

def create_webdriver():
    """
    Create and return a Chrome web driver for use in this app's scraping functions.

    We're using a webdriver instead of just raw requests, because yahoo finance income statement rows
    sometimes need to be expanded with an HTML button (like OpEx).
    """
    print("Creating web driver...")
    # Specify the file of the driver to be used
    driver_name = 'chromedriver.exe'

    # Instantiate driver options
    options = webdriver.ChromeOptions()

    # Specify driver options
    options.add_argument('--headless')
    options.add_argument('--ignore_certificate_errors')
    options.add_argument('--incognito')
    options.add_argument('--log-level=3')

    # Instantiate driver service
    service = Service(WEBDRIVER_PATH + driver_name)

    # Instantiate driver
    driver = webdriver.Chrome(service = service, options = options)

    return driver

def expand_statement_rows(webdriver, levels = 1):
    """
    Get all rows of a financial statement in expansion order.
    Get rows -> expand rows -> get rows, etc. until iterator runs out.

    Intended as a helper function of get_statement_rows() in this module.
    """
    statement_rows = list()

    for i in range(levels):
        # Find buttons that haven't been clicks, yet. Sections that haven't been expanded.
        # These are marked by an arrow icon pointing to the right
        # Expanded rows are marked by arrow icon pointing down
        # This makes sure we aren't double counting rows after we expand them.
        buttons = webdriver.find_elements(By.XPATH, '//div[@data-test="fin-row"]//*[local-name()="svg" and @data-icon="caret-right"]')
        soup = BeautifulSoup(webdriver.page_source, 'lxml')
        statement_rows += soup.find_all('div',{'data-test':'fin-row'})
        if i < levels - 1:
            for button in buttons:
                button.click()

    return statement_rows, soup

def get_statement_rows(webdriver, ticker_symbol, statement_name):
    """
    Get income statement for company = ticker_symbol from yahoo finance.

    Only returns the set of divs on the page corresponding to income statement rows and its header.

    Recommended use case is passing the output to the following dictify_income() function to get a proper
    income statement dict with many more use cases.

    Statement name takes one of 3 values: is, bs, cfs. Determines how button clicking/row expansion will work.
    """
    statement_pages = {
    'is':'financials',
    'bs':'balance-sheet',
    'cfs':'cash-flow'
    }

    print("Requesting statement DOM from Yahoo Finance...")
    url = 'https://finance.yahoo.com/quote/{}/{}'.format(ticker_symbol,statement_pages[statement_name])
    # Open the page in webdriver
    webdriver.get(url)

    # Expand the OpEx row on the page, if getting income statement
    desired_levels = {
    'is':2,
    'bs':3,
    'cfs':2
    }

    # Throw an error when statement name is invalid to call out the reason
    # expand_statement_rows() will break, below.
    if statement_name not in desired_levels.keys():
        raise ValueError('Invalid statement name provided. Should be is, bs or cfs. Is {}'.format(statement_name))

    while len(webdriver.find_elements(By.XPATH, '//button')) == 0:
        # building in a second of pause to let the page load before attempting the click
        # assumption is that statement will always have at least one expandable row in it
        # if no expandable rows visible, assume page hasn't loaded
        sleep(1)
    sleep(1) # pause an extra second, because this is still failing to work

    statement_rows, soup = expand_statement_rows(webdriver, levels = desired_levels[statement_name])

    # Get the income statement's heading
    statement_heading = soup.find('div',{'class':'D(tbhg)'}).select_one('div:first-child').find_all('div')

    # Get list of divs from the page source that correspond to income statement rows


    return statement_heading, statement_rows

def dictify_statement(statement_heading, statement_rows, ticker_symbol, skip_rows = None):
    """
    Takes a statement heading and a list of statement rows as returned by get_statement().
    Literally, these are sets of divs from the yahoo finance page's dom.

    Gets rid of all the dom baggage and returns a simple dict of statement rows.

    ticker_symbol just lets this function create a top-level dict entry for the
    name of the company. This will help functions that operate on multiple company
    objects understand which company the object belongs to.
    """
    print("Parsing statement DOM...")
    # Instantiate the income_dict
    statement_dict = dict()
    # Instantiate a subtotal row component lookup dict for later
    subrows_dict = dict()

    ## STEP 1: Get the years column before doing anything else. Requires special process.
    # We take indices [2:], because first two columns are the row name ("breakdown") and a blank column for formatting
    statement_dict['year'] = np.array([x.text for x in statement_heading[2:]])

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
            rowname = clean_statement_heading(row.select_one('div:first-child').find_all('div')[0].text)

            # get all values from skip_rows into a single list to let us
            # skip those rows in the following step
            skip_vals = []
            for x in list(skip_rows.values()):
                skip_vals += x

            if skip_rows != None:
                if rowname not in [clean_statement_heading(x) for x in skip_vals]:
                    statement_dict[rowname] = rowvals

    dictified_statement = dict(company = ticker_symbol, groupings = dict(), statement = statement_dict)

    return dictified_statement

def scrape_statement(ticker, statement, skip_rows):
    """
    Run all necessary functions above to get an income statement dict at once.

    statement argument: is, bs or cfs. (income, balance, cash flow)
    """
    print('Getting {} statement for {}...'.format(statement, ticker))
    driver = create_webdriver()
    statement_heading, statement_rows = get_statement_rows(driver, ticker, statement)
    statement_dict = dictify_statement(statement_heading, statement_rows, ticker, skip_rows)
    print('\n')
    return statement_dict
