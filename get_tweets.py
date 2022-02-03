from searchtweets import (gen_request_parameters, load_credentials,
                          collect_results)
import pandas as pd

search_args = load_credentials("~/.twitter_keys.yaml",
                               yaml_key="search_tweets_v2",
                               env_overwrite=False)


def get_tweets(wordle_num, max_tweets=3000, return_df=False):
    """Helper function, requires searchtweets v2 and proper Twitter api credentials. Turns a single wordle
    query into a dataframe that can be used inside the TwitterWordle class."""
    query = gen_request_parameters(f"Wordle {wordle_num}",
                                   granularity=None,
                                   results_per_call=100)

    tweets = collect_results(query,
                             max_tweets=max_tweets,
                             result_stream_args=search_args)
    all_tweet_text = []
    for l in tweets:
        all_tweet_text.extend([x['text'] for x in l['data']])
    if return_df:
        return pd.DataFrame([{
            'tweet_text': x,
            'wordle_id': wordle_num
        } for x in all_tweet_text])
    else:
        return all_tweet_text
