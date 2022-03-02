import zipfile
import pandas as pd
from sqlalchemy import create_engine, types
from first_word import get_first_words, wordle_lookup, make_first_guest_list

if __name__ == "__main__":
    df = make_first_guest_list()
    dbc = create_engine('sqlite:///wordle_first_words.db')
    dtype_dict = {
        'score': types.TEXT,
        'target': types.TEXT,
        'guess': types.INTEGER,
        'score_frequency_rank': types.FLOAT,
        'wordle_num': types.INTEGER,
        'guess_count': types.INTEGER,
        'commonalitiy': types.INTEGER,
        'weighted_rank': types.FLOAT,
    }

    df.to_sql('main',
              dbc,
              if_exists='replace',
              dtype=dtype_dict,
              index=False,
              chunksize=10000,
              method='multi')
