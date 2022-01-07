from forex_python.converter import CurrencyRates
from definitions import ASSET_PATH
from modules.files import save_json
from datetime import datetime

from bs4 import BeautifulSoup
import requests as r

import numpy as np

from datetime import datetime, timedelta

import csv

def scrape_conversion_rates(currency_a, currency_b, save = False):
    """
    Alternative to get_conversion_rates(). get calls forex-python api. It's quick,
    but it only goes back to 2000.

    This method scrapes a history table on fxtop.com and goes back to 1953.
    This method can be used to maintain 40-year analysis time frames in
    non-USD financial statements.
    """
    url = 'https://fxtop.com/en/historical-exchange-rates.php?A=1&C1={}&C2={}&YA=1&DD1=&MM1=&YYYY1=&B=1&P=&I=1&DD2=07&MM2=01&YYYY2=2022&btnOK=Go!'.format(currency_a.upper(), currency_b.upper())

    print('Getting webpage...')
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    print('Done! parsing dom...')
    # forex table is nested two tables down. but it's only table with border of 1
    forex_table = soup.find('table', {'border':1}).find_all('tr')[1:] # skip the header row

    conversion_rates = dict()
    for row in forex_table:
        year = int(row.find_all('td')[0].text)
        value = float(row.find_all('td')[1].text)
        conversion_rates[year] = value

    if save:
        filename = currency_a.lower() + '_to_' + currency_b.lower() + '.json'
        save_json(conversion_rates, ASSET_PATH + filename)

        print('Saving to {}'.format(ASSET_PATH + filename))

    return conversion_rates

def get_conversion_rates(currency_a, currency_b, year, granularity = 15):
    """
    Using forex-python package, gather forex rates from currency_a to currency_b
    in year by granularity.

    Gets the average exchange rate in the year by taking measurements at
    granularity increments throughout the year. Granularity is measured in days.
    A granularity of 15 takes the rate every 15 days for the year specified.

    currency_a and currency_b are strings. currency codes. Yen is 'JPY'. US
    Dollar is 'USD'.
    """
    c = CurrencyRates()

    # Get a list of the dates at which points the forex rates should be collected
    # Will iterate over this list to gather forex rates in the next step
    date_list = [datetime(year, 1, 1) + timedelta(days = granularity * x) for x in range(int(365.25/granularity))]

    rate_list = np.asarray([])
    for date in date_list:
        print(date)
        rate = c.get_rate(currency_a, currency_b, date)
        rate_list = np.append(rate_list, rate)

    return rate_list

def trend_mean_rates(currency_a, currency_b, last_year, first_year = 2000, save = False):
    """
    NOTE: Effectively deprecated in favor of scrape_conversion_rates(), which is
    much faster. Leaving this function in here, because the scraping method will be
    outdated one day when fxtop.com change their DOMs. This will work in a pinch.

    Get a dictionary mapping years to mean conversion rate from a to b in those years.

    np.asarray(list(dict.values())) can be used to get a multiplier array. This array
    can be used to translate financial statements from currency_a to currency_b.

    currencies are strings.

    Optionally saves the resulting json object to this project's assets folder.

    years are ints.
    """
    # Correct any first_date < 2000. forex-python doesn't go back further than that.
    assert first_year >= 2000, 'ERROR: forex-python package only has forex rates back to 2000. Choose a year that is at least 2000.'

    trend_dict = dict()
    for year in range(first_year, last_year + 1):
        mean_rate = get_conversion_rates(currency_a, currency_b, year).mean()
        trend_dict[year] = mean_rate

    if save:
        filename = currency_a.lower() + '_to_' + currency_b.lower() + '.json'
        save_json(trend_dict, ASSET_PATH + filename)

    return trend_dict

def get_cpiu(year = 0, item = 'CUSR0000SA0'):
    """
    Gets raw data from the bureau of labor statistics (BLS).

    Traces consumer price index (CPI) for all urban consumers (-U) since 1947.

    BLS recommends this as the basis of inflation adjustmentsj, so this
    is intended as a helper function to normalize_statements() method of
    the company() class.

    If a year is provided, get monthly CPI-U values for that year. Turns
    this function into a helper function of get_infation_rate() to follow.

    NOTE: Item is broken. Don't change it outside the default. Need to gather
    several reports from bureau of labor stats and build a lookup dict from them.
    Dict item suffix = report url. ('SA0':allitemsurl). This function can then
    gather the correct report based on the item suffix provided in the item arg.

    CUSR0000SA0 is CPI-U for all items, '0000' part means US city average.
    """
    # Keeping both URLs in here. Developer can change value in .get() below as needed.
    bls_url = 'https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems'
    dataset = parse_bls_report(bls_url)
    # Filter dataset for "all items" (SA0) and January (M01)
    # All items is the big bucket of consumer items. The super CPI-U
    # Good benchmark to apply to all industries
    # Just take January, because simpler and just as useful as getting an average
    # Need a single CPI-U value for each year
    if year:
        dataset_filtered = [x for x in dataset if x[0] == item and x[1] == str(year) and x[2].startswith('M')]
        cpiu = dict()
        for row in dataset_filtered:
            cpiu[row[1] + row[2]] = float(row[3])
    else:
        dataset_filtered = [x for x in dataset if x[0] == item and x[2] == 'M01']
        cpiu = dict()
        for row in dataset_filtered:
            cpiu[row[1]] = float(row[3])

    return cpiu

def parse_bls_report(report_url):
    """
    Helper function that takes reports at bureau of labor stats site (CPI-U)
    and converts them to a list of rows from the dataset.
    """
    response = r.get(report_url)
    data = response.text.splitlines()

    dataset = []
    reader = csv.reader(data, delimiter = '\t')
    for line in reader:
        dataset.append([x.strip() for x in line])

    return dataset

def get_cpiu_items():
    """
    Gets a dict of all CPI-U items measured by the US Bureau of Labor Stats.

    Each item is a different "shopping cart" of goods. Use the item most relevant
    to a company's industry in order to track inflation against its financial
    statement values.

    This dict is meant to be a way to lookup values to feed into get_cpiu() or
    get_inflation() as the item argument.
    """
    bls_url = 'https://download.bls.gov/pub/time.series/cu/cu.item'

    data = parse_bls_report(bls_url)

    cpiu_items = dict()
    for row in data[1:]: # skip first row of column names
        cpiu_items[row[0]] = row[1]

    return cpiu_items

def get_inflation(year = datetime.today().year, item = 'CUSR0000SA0'):
    """
    Get inflation rate for a year.

    Default is current year.

    Uses get_cpiu() to get provided year's monthly CPI-U values.
    Inflation rate is percent difference between earliest recorded month and
    latest recorded month.

    NOTE: Item is broken. Don't change it outside the default. Need to gather
    several reports from bureau of labor stats and build a lookup dict from them.
    Dict item suffix = report url. ('SA0':allitemsurl). This function can then
    gather the correct report based on the item suffix provided in the item arg.
    """
    cpiu = get_cpiu(year = year, item = item)

    latest = cpiu[max(cpiu.keys())]
    earliest = cpiu[min(cpiu.keys())]

    inflation_rate = (latest - earliest) / earliest

    return inflation_rate

def get_cpiu_sources():
    """
    Visit several known bureau of labor stats reports and gather the item codes
    in them. Map those codes to the report URLs so that get_inflation() and
    get_cpiu() can use the resulting dict as a lookup source before collecting
    their data.
    """
    # STEP 1: Define list of report URLs
    report_urls = [
    'https://download.bls.gov/pub/time.series/cu/cu.data.11.USFoodBeverage',
    'https://download.bls.gov/pub/time.series/cu/cu.data.12.USHousing',
    'https://download.bls.gov/pub/time.series/cu/cu.data.13.USApparel',
    'https://download.bls.gov/pub/time.series/cu/cu.data.14.USTransportation',
    'https://download.bls.gov/pub/time.series/cu/cu.data.15.USMedical',
    'https://download.bls.gov/pub/time.series/cu/cu.data.16.USRecreation',
    'https://download.bls.gov/pub/time.series/cu/cu.data.17.USEducationAndCommunication',
    'https://download.bls.gov/pub/time.series/cu/cu.data.18.USOtherGoodsAndServices',
    'https://download.bls.gov/pub/time.series/cu/cu.data.20.USCommoditiesServicesSpecial'
    ]

    # STEP 2: Iterate through report URLs, getting data from each
    cpiu_sources = dict()
    for url in report_urls:
        data = parse_bls_report(url)
        # STEP 3: get first item in each row (the item code).
        for row in data:
            item = row[0]
            # STEP 4: Append dict[item_code] = report_url
            cpiu_sources[item] = url

    return cpiu_sources
