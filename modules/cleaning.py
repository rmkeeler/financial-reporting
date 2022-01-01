# Math packages
import numpy as np

# Text parsing packages
import re

# Date processing packages
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

def rewrite_value(statement, row_name, indices, values):
    """
    Helper function of fill_ttm() method of company() class.

    args:
        statement: financial statement dictionary like company.income_statement['statement']
        row_name: name of a financial statement row as appears on yahoo finance (case sensitive)
        indices: numeric values array-like of the index of the value to replace in the statement row
        value: the values (array-like) to fill at the given index in the given row_name in the statement

    returns: new_statement, revised statement dict with value filled at row_name.
    Can be used as a direct replacement for company.statement['statement'].
    """
    new_statement = statement
    np.put(new_statement[row_name], indices, values)

    return new_statement

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

def unclean_statement_heading(heading):
    """
    Undoes what happens in clean_statement_heading() in this module.

    Separate with spaces and all caps.
    """

    new_heading = re.sub('_',' ',heading).upper()

    return new_heading

def clean_statement_heading(heading):
    """
    Helper function of dictify_statement(). Cleans out normal garbage from
    table heading strings.
    """
    clean_heading = re.sub(' ','_',heading).replace('&','and').lower()

    return clean_heading

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

def get_dictkey(val, dictlike):
    """
    Takes a value expected to appear in a given dictionary.

    Returns that value's key.
    """
    for key, value in dictlike.items():
        if value == val:
            return key
        else:
            print('val not found...')

def listify_nparrays(nparray):
    """
    Pass this to json.dump() as the default function for data it can't handle.
    Numpy arrays are non-serializable in JSON, so json.dumps() is failing
    when I try to save financial statement attributes.

    Checks the object passed to it to see if it's a np array. If it is, it
    converts the np array to a python list.
    """
    if isinstance(nparray, np.ndarray):
        return nparray.tolist()
