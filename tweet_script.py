import argparse
import config
import tweepy
import json
from TwitterWordle import TwitterWordle
import pandas as pd
from get_tweets import get_tweets

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Wordle')
    parser.add_argument('wordle_num', type=int, help='number of wordle')
    parser.add_argument('--no-tweet',
                        action='store_true',
                        help='no tweet',
                        default=False)
    args = parser.parse_args()
    try:
        df = pd.read_parquet(f"wordle{args.wordle_num}.parquet")
    except FileNotFoundError:
        df = get_tweets(args.wordle_num, return_df=True)

    t = TwitterWordle(df, use_limited_targets=False)

    auth = tweepy.OAuthHandler(config.api_key, config.api_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)
