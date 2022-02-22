import pickle
import numpy as np
from collections import Counter
import pandas as pd
import numpy as np
import re
import hashlib
import json


def help_hash(x):
    return hashlib.sha256(x.encode()).hexdigest()


def flatten_list(list_of_lists):
    return [y for x in list_of_lists for y in x]


def check_match(x):
    if re.search(r"Wordle \d{3}", x) and len(
            re.findall("wordle", x,
                       re.IGNORECASE)) == 1 and ('https' not in x.lower()):
        return True
    return False


class TwitterWordle():
    last_figure = None

    def __init__(self, tweet_df=None, use_limited_targets=True):
        if use_limited_targets:
            self.zipped_counters = json.load(
                open("zipped_counters_nyt_2022_02_15.json", "r"))
        else:
            self.zipped_counters = pickle.load(
                open("zipped_counters_allwords_nyt.pickle", "rb"))
        self.output = []
        self.zipped_counters = {key: val for key, val in self.zipped_counters}
        print(
            f"Loaded {len(self.zipped_counters)} pre-computed lookup dictionaries."
        )
        if tweet_df is not None:
            assert isinstance(tweet_df, pd.DataFrame), 'Must be a dataframe'
        self.tweet_df = tweet_df
        if self.tweet_df is not None:
            self.tweet_df = self.tweet_df.loc[
                tweet_df.loc[:, 'tweet_text'].apply(check_match)]
            self.tweet_df['score_list'] = self.tweet_df['tweet_text'].apply(
                self.wordle_guesses)
            self.tweet_df = self.tweet_df.loc[
                self.tweet_df.loc[:,
                                  'score_list'].apply(lambda x: len(x) <= 6)]
        with open("hashed_lookup2.json", "r") as data_file:
            self.solution_dict = json.load(data_file)

    def print_store(self, s, **kwargs):
        self.output.append(s)
        print(s, **kwargs)

    @staticmethod
    def process_counter(target_dictionary, c, penalty_term=-5E7, min_count=3):
        """process the counter of the tweet guesses vs the target word dictionary. A penalty term will reduce the score of
        impossible guesses for the target word but shouldn't penalize the true word if a few tweets are spurious.
        
        The target_dictionary contains weighted values for each possible guess for 1 target word.
        
        So how many words can produce 🟩⬛⬛🟩⬛ for a given target and are any of those common words or are they all 
        obscure words unlikely to be guessed?

        This takes for each target dictionary the sum of the guesses made in public, above the_min_count

        Weighing by the count of how often the guess appears or only using the most common guessess produced incorrect results.

        Min_count can be 1 if the tweet sample size is small.
        
        """
        if not penalty_term:
            penalty_term = -np.std(list(target_dictionary.values())) * .5

        return sum([
            target_dictionary.get(
                guess, penalty_term
            )  # one would think weighing the penalty term by how often it occurs
            # would help. if 300 people got a line score that's impossible, that can't be the word.
            # in practice weighing by the frequency doesn't seem to help. specifically, wordle 215 returned 'rabid' when I
            # weighed the penalty term by how often the score line occurred.
            for guess, the_count in c.most_common() if the_count >= min_count
        ])

    def extract_all_guesses(self, wordle_num, downsample=None, verbose=True):
        """for the dataframe, extract the guesses for wordle_num into a single list"""
        if not downsample:
            if verbose:
                self.print_store(
                    f"TwitterWordle analyzed {len(self.tweet_df.query(f'wordle_id == {wordle_num}'))} tweets for Wordle {wordle_num}.\n"
                )
            return flatten_list(
                self.tweet_df.query(f'wordle_id == {wordle_num}')
                ['score_list'].tolist())

        return flatten_list(
            self.tweet_df.query(f'wordle_id == {wordle_num}').sample(
                downsample, random_state=42)['score_list'].tolist())

    @staticmethod
    def wordle_guesses(tweet):
        text = (tweet.replace("🟩",
                              "2").replace("🟨",
                                           "1").replace("⬛",
                                                        "0").replace("⬜", "0"))
        guesses = re.findall("([012]{5})", text)
        return guesses

    def solve_guess_list(self,
                         all_guesses,
                         min_count=None,
                         verbose=True,
                         exclude_misses=False,
                         **kwargs):
        """take a list of all tweeted guesses and return the result, the sigma, and the Series."""
        if not exclude_misses:
            the_guesses = [x for x in all_guesses if x != '22222']
        else:
            self.print_store("Excluding misses")
            the_guesses = [
                x for x in all_guesses if x not in ('22222', '00000')
            ]

        c = Counter(the_guesses)
        if not min_count:
            min_count = np.floor(np.quantile(list(c.values()), .25))
        if verbose:
            self.print_store(
                f"{len(the_guesses)} score patterns. {len(set(the_guesses))} unique.\n"
            )

        res = []
        for key, val in self.zipped_counters.items():
            res.append({
                'sum':
                self.process_counter(val, c, min_count=min_count, **kwargs),
                'word':
                key
            })
        res = pd.DataFrame(res).set_index('word').sort_values('sum')['sum']
        # self.print_store(res.describe())
        res = (res / res.mean()) - 1
        return res.index[-1], res.max() / res.std(), res, (
            res.iloc[-1] / res.iloc[-2]), the_guesses

    def solve(self,
              wordle_num=None,
              tweet_list=None,
              plot=False,
              downsample=None,
              min_count=3,
              iterate_low_score=True,
              exclude_misses=False,
              return_full_plot=False,
              mask_result=True,
              **kwargs):
        """Can extract a tweet from self.tweet_df or process a list of tweets"""

        assert wordle_num or tweet_list, "Must provide either a wordle_num or a list of tweets"
        self.output = []
        if wordle_num:
            assert self.tweet_df is not None, "Class must be instantiated with a dataframe to solve from a wordle number"
            score_guess_list = self.extract_all_guesses(wordle_num,
                                                        downsample=downsample)
        elif tweet_list:
            self.print_store(f"{len(tweet_list)} tweets")
            score_guess_list = flatten_list([
                self.wordle_guesses(x)
                for x in [x for x in tweet_list if check_match(x)]
            ])

        prediction, sigma, data, delta_above_two, the_guesses = self.solve_guess_list(
            score_guess_list,
            min_count=min_count,
            exclude_misses=exclude_misses,
            **kwargs)
        iterated_results = []
        if delta_above_two < 1.1 and iterate_low_score:
            print(
                f'Wordle {wordle_num} initial signal low {delta_above_two:1.3}. Iterating for better parameters'
            )

            for my_min_count in range(max(min_count - 2, 1), min_count + 10,
                                      2):
                if delta_above_two > 1.1:
                    continue

                for p in range(-7, -100, -2):
                    print(".", end="")

                    penalty_term = p * 1E7
                    if delta_above_two > 1.1:
                        continue
                    prediction, sigma, data, delta_above_two, the_guesses = self.solve_guess_list(
                        score_guess_list,
                        min_count=my_min_count,
                        penalty_term=penalty_term,
                        verbose=False)
                    final_min_count = my_min_count
                    final_penalty_term = penalty_term
                    iterated_results.append(
                        (prediction, sigma, data, delta_above_two))
            print(
                f"\nIterated to a better signal with min_count {final_min_count} and penalty {final_penalty_term:.2E}"
            )
        if delta_above_two < 1.1 and iterate_low_score:
            prediction, sigma, data, delta_above_two = sorted(
                iterated_results, key=lambda x: x[3])[-1]
        prediction_dict = self.zipped_counters.get(prediction)
        numerator = len(set(the_guesses))
        denom = len(prediction_dict)
        impossible_count = len(
            set(the_guesses).difference(set(prediction_dict.keys())))
        self.print_store(
            f"{(numerator-impossible_count) / denom:.2%}, ({numerator-impossible_count}/{denom}) valid final guess patterns found. Impossible pattern count: {impossible_count}.\n"
        )

        if not mask_result:
            self.print_store(
                f"Wordle {wordle_num} prediction: {prediction.upper()}.")
            self.print_store(
                f"{sigma:.2} STD above mean. {delta_above_two:.3} above runner up.\n"
            )
            fig = self.make_figure(return_full_plot, data)
            return_val = prediction
        else:
            self.print_store(
                f'Wordle {wordle_num} solution hash: {help_hash(prediction)}. {sigma:.2} STD above mean. {delta_above_two:.3} above runner up.\n'
            )
            self.print_store(
                f"Solution match is {str(help_hash(prediction) == self.solution_dict[str(wordle_num)]).upper()}"
            )
            plot_data = data.sort_values().tail(20)
            plot_data.index = [help_hash(x)[:7] for x in plot_data.index]
            fig = self.make_figure(return_full_plot, plot_data)
            return_val = help_hash(prediction)
        #self.print_store(f"Wordle {wordle_num} score: {sigma:.2} STD above mean. {delta_above_two:.3} above runner up.\n")
        if plot:
            fig.show()
        self.last_figure = fig
        return return_val

    def solve_all(self, **kwargs):
        if self.tweet_df is not None:
            for wordle_num in sorted(self.tweet_df['wordle_id'].unique()):
                self.solve(wordle_num, **kwargs)

    def make_figure(self, make_full_plot, data):
        if make_full_plot:
            return data.sort_values().plot.bar(labels={
                'index': 'Hashed Word',
                'value': 'Normalized Score'
            })
        else:
            return data.sort_values().tail(20).plot.bar(
                labels={
                    'index': 'Hashed Word',
                    'value': 'Normalized Score'
                })

    def show_bad_tweets(self, answer, wordle_num):
        all_guesses = self.extract_all_guesses(wordle_num)

        bad_guesses = set(all_guesses).difference(
            set(self.zipped_counters[answer].keys()))

        thelocs = self.tweet_df['score_list'].apply(
            lambda x: any(y in x for y in bad_guesses))

        print(bad_guesses)

        for x in (self.tweet_df.loc[thelocs].query('wordle_id == @wordle_num')
                  ['tweet_text']):
            print('------')
            print(x)

    def make_bad_df(self, answer, wordle_num):
        all_guesses = self.extract_all_guesses(wordle_num)

        bad_guesses = set(all_guesses).difference(
            set(self.zipped_counters[answer].keys()))

        thelocs = self.tweet_df['score_list'].apply(
            lambda x: any(y in x for y in bad_guesses))

        print(bad_guesses)

        return self.tweet_df.loc[thelocs].query('wordle_id == @wordle_num')