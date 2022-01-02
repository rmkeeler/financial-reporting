from forex_python.converter import CurrencyRates
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

def trend_mean_rates(currency_a, currency_b, first_year, last_year):
    """
    Get a dictionary mapping years to mean conversion rate from a to b in those years.

    np.asarray(list(dict.values())) can be used to get a multiplier array. This array
    can be used to translate financial statements from currency_a to currency_b.

    currencies are strings.

    years are ints.
    """
    trend_dict = dict()
    for year in range(first_year, last_year + 1):
        mean_rate = get_conversion_rates(currency_a, currency_b, year).mean()
        trend_dict[year] = mean_rate

    return trend_dict
