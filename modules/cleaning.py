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

def align_arrays(reference_a, reference_b, subject_array_b):
    """
    Common problem in this project is statements or companies with different
    numbers of years of data.

    Common solution is to align both entities (statements, companies) to the one
    with the fewest years available.

    This means figuring out which years they have in common and then filtering
    row np arrays for indices that coincide with the indices of the shared years
    in common.

    args:
        reference_a, b: lists (usually year_adjusted is used). These list-likes
        are contrasted to find the values in common and the indices of those
        values in reference_b.

        subject_array_b: This array will be filtered for the indices returned
        from reference_b that represent values also contained in refrence_a.

    example:
        reference_a is balance sheet years from 1985-2020.
        reference_b is cash flow years from 1989-2021.
        subject_array_b is operating_cash_flow array in cash flow statement
        Filter subject_array_b for the indices in reference_b that correspond
        to the years 1989-2020.

        To apply this function, iterate through statement rows (subject_array_b)
        in a statement, then do it again to the other statement.
    """
    mask = [i for i, x in enumerate(reference_b) if x in reference_a]

    if isinstance(subject_array_b, list):
        aligned_subject = [x for i, x in enumerate(reference_b) if i in mask]
    elif isinstance(subject_array_b, np.ndarray):
        aligned_subject = subject_array_b[mask]

    return aligned_subject
