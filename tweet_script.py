import argparse
from config import *
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

    api = tweepy.Client(consumer_key=api_key,
                        consumer_secret=api_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret)

    ## need to make code to check date and tweet log reply to yesterday as well as upload the log?