import argparse
import config
import tweepy
import json
from TwitterWordle import TwitterWordle
import pandas as pd
from get_tweets import get_tweets
import io
import datetime


def today_wordle_num():

    wordle_start = datetime.datetime(2021, 6, 19)
    now = datetime.datetime.now()

    return (now - wordle_start).days


if __name__ == '__main__':
    pd.options.plotting.backend = "plotly"
    parser = argparse.ArgumentParser(description='Wordle')
    parser.add_argument('solution', type=str, help='wordle solution')

    parser.add_argument('wordle_num', type=int, help='number of wordle')
    parser.add_argument('--no-tweet',
                        action='store_true',
                        help='no tweet',
                        default=False)

    parser.add_argument('--use-full-dictionary',
                        action='store_true',
                        help='use the full 12k word dictionary',
                        default=False)
    args = parser.parse_args()
    try:
        df = pd.read_parquet(f"wordle{args.wordle_num}.parquet")
    except FileNotFoundError:
        df = get_tweets(args.wordle_num, return_df=True)
        df.to_parquet(f"wordle{args.wordle_num}.parquet")

    t = TwitterWordle(df, use_limited_targets=not args.use_full_dictionary)
    prediction = t.solve(args.wordle_num, mask_result=False, min_count=4)
    if prediction == args.solution:
        emoji = '✅'
    else:
        emoji = '❌'

    img_bytes = t.last_figure.to_image(format="png")
    io_obj = io.BytesIO(img_bytes)
    auth = tweepy.OAuthHandler(config.api_key, config.api_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)

    def add_emoji(line):
        if 'prediction' in line:
            return line + f" {emoji}"
        return line

    tweet_text = '\n'.join([add_emoji(x) for x in t.output])
    print(tweet_text)
    if not args.no_tweet:
        assert args.wordle_num != today_wordle_num(
        ), "Can't tweet today's wordle"
        try:
            with open('better_history.json') as f:
                history = json.load(f)
        except:
            history = []
        result = api.update_status_with_media(
            status=tweet_text,
            file=io_obj,
            filename=f'wordle{args.wordle_num}.png')
        history.append({
            'wordle_num': args.wordle_num,
            'id': result.id,
            'success': emoji == '✅',
            'solution': args.solution,
            'text': tweet_text,
            'timestamp': result.created_at.isoformat()
        })
        with open('better_history.json', 'w') as f:
            json.dump(history, f, indent=4)
