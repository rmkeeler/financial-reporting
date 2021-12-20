import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

def adjust_date(date_string, relativemonths = 1, direction = -1):
    """
    Helper function of plot_companies() in this module.
    Not all companies publish financial statements on 12/31.
    Some do so on 1/31.

    Effectively, 12/31 peformance and 1/31 performance line up.
    At least as far as trending is concerned.

    To make company metrics more plottable, this function adjusts all dates
    in statement['statement']['year'] back one month, then extracts the year and
    converts to text. This tends to line up everyone's reporting periods.

    args:
        date_string: string in format %m/%d/%Y (1/31/2020, for example).
        relativemonths: number of months to add or subtract from a date.
        direction: 1 for add, -1 for subtract

    returns:
        adjusted year: String of year after adjustment is made to the date.
    """
    date = dt.strptime(date_string, '%m/%d/%Y')
    newdate = date + (direction * relativedelta(months = relativemonths))
    adjusted_year = str(newdate.year)

    return adjusted_year

def plot_companies(companies, metric):
    """
    Takes a list of company statements (dicts from company class) and a string
    that corresponds to an item in the dictionaries to plot.

    Pass statement['metrics'] or statement['statement'], for example.
    """
    fig = None
    return fig
