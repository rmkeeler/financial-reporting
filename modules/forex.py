from forex_python.converter import CurrencyRates
from definitions import ASSET_PATH
from modules.files import save_json
import numpy as np
from datetime import datetime, timedelta

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
