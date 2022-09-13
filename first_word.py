import pandas as pd
from TwitterWordle import TwitterWordle, check_match
from helper import get_num_line, stringify, make_freqs
import zipfile
from IPython.display import display, HTML

import json
import config

image_mapping_dict = {1: "🟨", 0: "⬜", 2: "🟩"}


def format_df(df, **kwargs):
    """format the dataframe for display without index"""
    display(HTML(df.to_html(index=False, **kwargs)))


def map_to_emoji(pattern):
    return ''.join([image_mapping_dict[int(x)] for x in pattern])


pattern_lookup_dict = {
    key: val
    for key, val in json.load(open("zipped_counters_nyt_2022_02_15.json", "r"))
}


def better_wordle_solutions():
    wordle_lookup = {
        i: x
        for i, x in enumerate(
            pd.read_csv(config.wordle_solution_file_path, header=None)
            [0].tolist())
    }
    new_dict = pd.read_json("../wordle_public/better_history.json").set_index(
        'wordle_num')['word'].to_dict()
    wordle_lookup.update(new_dict)
    wordle_lookup.update({
        335: 'gamer',
        401: 'elope',
        402: 'cinch',
        420: 'hunky',
        361: 'atone',
        365: 'cacao',
        368: 'gloat',
        370: 'brink',
        386: 'stead',
        388: 'madam',
    })
    return wordle_lookup


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
    reverse_map = {val: key for key, val in better_wordle_solutions().items()}

    df['score_list'] = df['tweet_text'].apply(TwitterWordle.wordle_guesses)
    short_words = pd.read_csv('wordle-all_2022-02-15.txt', header=None)[0]
    df['first_score'] = df['tweet_text'].apply(try_fail)

    df['answer'] = df['wordle_id'].map(better_wordle_solutions())
    df['valid'] = df[['score_list', 'answer'
                      ]].apply(lambda x: flag_possible_only(x[0], x[1]),
                               axis=1)
    out = []
    pre_filter_ln = len(df)
    df = df.loc[df.loc[:, ['tweet_text', 'wordle_id']].apply(check_match,
                                                             axis=1)]
    df = df.loc[df.loc[:, 'score_list'].apply(lambda x: len(x) <= 6)]

    df = df.query('valid == True')
    print(f"Filtered out {pre_filter_ln - len(df)} of {pre_filter_ln} rows")
    for answer, _df in df.groupby('answer'):
        rank_lookup = _df['first_score'].value_counts().rank(
            ascending=False).to_dict()
        count_fraction_lookup = (
            _df['first_score'].value_counts() /
            _df['first_score'].value_counts().sum()).to_dict()
        temp_df = pd.DataFrame([{
            'score': stringify(get_num_line(x, answer)),
            'target': answer,
            'guess': x
        } for x in short_words])
        temp_df['score_frequency_rank'] = temp_df['score'].map(rank_lookup)
        temp_df['score_count_fraction'] = temp_df['score'].map(
            count_fraction_lookup)

        out.append(temp_df)
    df_concat = pd.concat(out)
    df_concat['wordle_num'] = df_concat['target'].map(reverse_map)
    df_concat['guess_count'] = df_concat.groupby(
        ['target', 'score'])['guess'].transform('count')
    return df_concat


def make_first_guest_list():
    with zipfile.ZipFile('wordle-tweets.zip') as myzip:
        tweets = pd.read_csv(myzip.open('tweets.csv'))
    print(f"Max wordle num {tweets['wordle_id'].max()}")
    first_guess_list = get_first_words(tweets)
    freq_map = make_freqs()

    first_guess_list['commonality'] = first_guess_list['guess'].map(freq_map)
    first_guess_list['weighted_rank'] = (
        first_guess_list['score_frequency_rank']**2)
    return first_guess_list
