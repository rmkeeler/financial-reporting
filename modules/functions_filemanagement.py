import pandas as pd

def save_dictlike(dictlike, filepath):
    """
    Takes a dictlike, converts it to dataframea and saves it as filename.

    Intended to be used in company class to save financial statements stored
    in object instances.
    """
    df = pd.DataFrame(dictlike)
    df.to_csv(filepath, index = False)
    return None
