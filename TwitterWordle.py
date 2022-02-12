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
    if re.search(r"Wordle \d{3}", x):
        return True
    return False


class TwitterWordle():
    def __init__(self, tweet_df=None, use_limited_targets=True):
        if use_limited_targets:
            self.zipped_counters = pickle.load(
                open("zipped_counters2.pickle", "rb"))
        else:
            self.zipped_counters = pickle.load(
                open("zipped_counters_allwords.pickle", "rb"))
        print(
            f"Loaded {len(self.zipped_counters)} pre-computed lookup dictionaries."
        )
        if tweet_df is not None:
            assert isinstance(tweet_df, pd.DataFrame), 'Must be a dataframe'
        self.tweet_df = tweet_df
        if self.tweet_df is not None:
            self.tweet_df = self.tweet_df.loc[tweet_df['tweet_text'].apply(
                check_match)]
        with open("hashed_lookup.json", "r") as data_file:
            self.solution_dict = json.load(data_file)

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
                print(
                    f"{len(self.tweet_df.query(f'wordle_id == {wordle_num}'))} tweets for wordle {wordle_num}"
                )
            return flatten_list([
                x
                for x in (self.tweet_df.query(f'wordle_id == {wordle_num}')
                          ['tweet_text'].apply(self.wordle_guesses)).tolist()
                if len(x) <= 6
            ])

        return flatten_list([
            x for x in (self.tweet_df.query(f'wordle_id == {wordle_num}')
                        ['tweet_text'].apply(self.wordle_guesses)
                        ).sample(downsample, random_state=42).tolist()
            if len(x) <= 6
        ])

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
            print("Excluding misses")
            the_guesses = [
                x for x in all_guesses if x not in ('22222', '00000')
            ]

        c = Counter(the_guesses)
        if not min_count:
            min_count = np.floor(np.quantile(list(c.values()), .25))
        if verbose:
            print(
                f"{len(the_guesses)} guess scores. {len(set(all_guesses))} unique. Min count : {min_count}"
            )

        res = []
        for key, val in self.zipped_counters:
            res.append({
                'sum':
                self.process_counter(val, c, min_count=min_count, **kwargs),
                'word':
                key
            })
        res = pd.DataFrame(res).set_index('word').sort_values('sum')['sum']
        # print(res.describe())
        res = (res / res.mean()) - 1
        return res.index[-1], res.max() / res.std(), res, (res.iloc[-1] /
                                                           res.iloc[-2])

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

        if wordle_num:
            assert self.tweet_df is not None, "Class must be instantiated with a dataframe to solve from a wordle number"
            score_guess_list = self.extract_all_guesses(wordle_num,
                                                        downsample=downsample)
        elif tweet_list:
            print(f"{len(tweet_list)} tweets")
            score_guess_list = flatten_list([
                self.wordle_guesses(x)
                for x in [x for x in tweet_list if check_match(x)]
            ])

        prediction, sigma, data, delta_above_two = self.solve_guess_list(
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
                    prediction, sigma, data, delta_above_two = self.solve_guess_list(
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

        if not mask_result:
            print(
                f"Wordle {wordle_num} prediction: {prediction.upper()}. {sigma:.2} STD above mean. {delta_above_two:.3} above runner up.\n"
            )
            fig = self.make_figure(return_full_plot, data)
            return_val = prediction
        else:
            print(
                f'Wordle {wordle_num} solution hash: {help_hash(prediction)}. {sigma:.2} STD above mean. {delta_above_two:.3} above runner up.\n'
            )
            print(
                f"Solution match is {str(help_hash(prediction) == self.solution_dict[str(wordle_num)]).upper()}"
            )
            plot_data = data.sort_values().tail(20)
            plot_data.index = [help_hash(x)[:7] for x in plot_data.index]
            fig = self.make_figure(return_full_plot, plot_data)
            return_val = help_hash(prediction)
        if plot:
            fig.show()
        return return_val

    def solve_all(self, **kwargs):
        if self.tweet_df is not None:
            for wordle_num in sorted(self.tweet_df['wordle_id'].unique()):
                self.solve(wordle_num, **kwargs)

    def make_figure(self, make_full_plot, data):
        if make_full_plot:
            return data.sort_values().plot.bar()
        else:
            return data.sort_values().tail(20).plot.bar()
