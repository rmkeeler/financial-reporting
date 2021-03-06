import json
import numpy as np
from modules.cleaning import get_dictkey, listify_nparrays
import os
from definitions import OUTPUT_PATH

def save_json(dictlike, filepath):
    """
    Take a dictionary (ideally the dict created by scrape_statement or import_statement)
    and save it to a json file.

    We keep file in json format, because json is way easier and lighter to pass
    around outside the app than a csv file/dataframe would. Many more processing
    possibilities.
    """
    statement = json.dumps(dictlike, default = listify_nparrays)

    with open(filepath, 'w') as f:
        f.write(statement)

    return None

def import_json(filepath):
    """
    Generic function for importing a JSON object from a JSON file on disk.
    """
    # Load in json
    with open(filepath) as f:
        data = json.load(f)

    return data

def import_statement_json(filepath):
    """
    Opens .json file at filepath and loads it into a python dictionary.

    Special instance of import_json() below that does some necessary data
    formatting particular to financial statement JSON objects containing np arrays.

    Converts lists in 'statement' key to nparray so that the company instance
    can function just like it does after scraping.

    List conversion just lets me store the data locally for use by other modules
    in this program (i.e. the future web app module).
    """
    # Load in the json file
    data = import_json(filepath)

    # Convert items to nparray if they're lists in the 'statement' key
    # These will always be lists of account amounts
    for key in data['statement'].keys():
        if isinstance(data['statement'][key], list) and key not in ['year', 'year_adjusted']:
            data['statement'][key] = np.array([float(x) if x != 'ttm' else x for x in data['statement'][key]])

    return data

def get_available_tickers():
    """
    Return a list of tickers and statements saved to the output directory.

    Intended to be used to remind one's self which companies have been stored so far.

    Or to make it easy to iterate through saved statements to update them in some way.
    """
    available_tickers = dict()
    output_files = os.listdir(OUTPUT_PATH)

    for f in output_files:
        ticker = f.split('_')[0]
        statement = f.split('_')[1].split('.')[0]
        if ticker in available_tickers.keys() and isinstance(available_tickers[ticker], list):
            available_tickers[ticker].append(statement)
        else:
            available_tickers[ticker] = [statement]

    return available_tickers
