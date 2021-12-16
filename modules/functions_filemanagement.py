import pandas as pd

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

def save_dictlike(dictlike, filepath, lookup = dict()):
    """
    Takes a dictlike, converts it to dataframe and restructures in long format.

    Then merges in any aggregate

    Then saves it as filename.

    Intended to be used in company class to save financial statements stored
    in object instances.
    """
    df = pd.DataFrame(dictlike)
    long_df = pd.melt(df, id_vars = ['year'], var_name = 'account', value_name = 'amount')

    if len(lookup.keys()) > 0:
        long_df['aggregated'] = long_df['account'].apply(lambda x: lookup[x] if x in lookup.keys() else x)

    long_df.to_csv(filepath, index = False)
    return None
