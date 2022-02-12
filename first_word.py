import pandas as pd
from TwitterWordle import TwitterWordle
from helper import get_num_line, stringify

wordle_lookup = {
    i: x
    for i, x in enumerate(
        pd.read_csv("../wordle_public/all_wordles.txt", header=None)
        [0].tolist())
}


def try_fail(x):
    try:
        return TwitterWordle.wordle_guesses(x)[0]
    except:
        return None


def get_first_words(df):
    reverse_map = {val: key for key, val in wordle_lookup.items()}
    short_words = pd.read_csv('wordle-dictionary-full.txt', header=None)[0]
    df['first_score'] = df['tweet_text'].apply(try_fail)

    df['answer'] = df['wordle_id'].map(wordle_lookup)
    out = []
    for answer, _df in df.groupby('answer'):
        count_lookup = _df['first_score'].value_counts().rank(
            ascending=False).to_dict()
        temp_df = pd.DataFrame([{
            'score': stringify(get_num_line(x, answer)),
            'target': answer,
            'guess': x
        } for x in short_words])
        temp_df['score_frequency_rank'] = temp_df['score'].map(count_lookup)
        out.append(temp_df)
    df_concat = pd.concat(out)
    df_concat['wordle_num'] = df_concat['target'].map(reverse_map)
    df_concat['guess_count'] = df_concat.groupby(
        ['target', 'score'])['guess'].transform('count')
    return df_concat