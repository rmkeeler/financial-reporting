import json
import numpy as np
from modules.cleaning import get_dictkey, listify_nparrays

def save_statement(dictlike, filepath):
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

def import_statement(filepath):
    """
    Opens .json file at filepath and loads it into a python dictionary.

    Converts lists in 'statement' key to nparray so that the company instance
    can function just like it does after scraping.

    List conversion just lets me store the data locally for use by other modules
    in this program (i.e. the future web app module).
    """
    # Load in the json file
    with open(filepath) as f:
        data = json.load(f)

    # Convert items to nparray if they're lists in the 'statement' key
    # These will always be lists of account amounts
    for key in data['statement'].keys():
        if isinstance(data['statement'][key], list) and key not in ['year', 'year_adjusted']:
            data['statement'][key] = np.array([float(x) if x != 'ttm' else x for x in data['statement'][key]])

    return data
