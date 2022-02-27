import pandas as pd
from TwitterWordle import TwitterWordle, check_match
from helper import get_num_line, stringify
import json

wordle_lookup = {
    i: x
    for i, x in enumerate(
        pd.read_csv("../wordle_public/all_wordles.txt", header=None)
        [0].tolist())
}

pattern_lookup_dict = {
    key: val
    for key, val in json.load(open("zipped_counters_nyt_2022_02_15.json", "r"))
}


def try_fail(x):
    try:
        return TwitterWordle.wordle_guesses(x)[0]
    except:
        return None


def flag_possible_only(score_pattern_list, answer):
    """returns false if a guess is impossible"""

    return all(
        pattern_lookup_dict.get(answer, {}).get(y) is not None
        for y in score_pattern_list)


def get_first_words(df):
    reverse_map = {val: key for key, val in wordle_lookup.items()}

    df['score_list'] = df['tweet_text'].apply(TwitterWordle.wordle_guesses)
    short_words = pd.read_csv('wordle-all_2022-02-15.txt', header=None)[0]
    df['first_score'] = df['tweet_text'].apply(try_fail)

    df['answer'] = df['wordle_id'].map(wordle_lookup)
    df['valid'] = df[['score_list', 'answer'
                      ]].apply(lambda x: flag_possible_only(x[0], x[1]),
                               axis=1)
    out = []
    pre_filter_ln = len(df)
    df = df.loc[df.loc[:, 'tweet_text'].apply(check_match)]
    df = df.loc[df.loc[:, 'score_list'].apply(lambda x: len(x) <= 6)]

    df = df.query('valid == True')
    print(f"Filtered out {pre_filter_ln - len(df)} of {pre_filter_ln} rows")
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