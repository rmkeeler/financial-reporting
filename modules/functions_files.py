import json
import numpy as np

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
        if isinstance(data['statement'][key], list) and key != 'year':
            data['statement'][key] = np.array([float(x) for x in data['statement'][key]])

    return data
