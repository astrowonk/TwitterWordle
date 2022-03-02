from collections import Counter
import pandas as pd
import numpy as np
import re

short_words = pd.read_csv('wordle-dictionary-full.txt',
                          header=None)[0].tolist()


def process_counter(target_dictionary, c, penalty_term=-5E7, min_count=5):
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
        for guess, the_count in c.most_common() if the_count > min_count
    ])


def flatten_list(list_of_lists):
    return [y for x in list_of_lists for y in x]


#modified from Kaggle project; get a list of results from a tweet
def wordle_guesses(tweet):
    text = (tweet.replace("Y",
                          "y").replace("🟩", "2").replace("M", "m").replace(
                              "🟨",
                              "1").replace("N",
                                           "n").replace("⬛",
                                                        "0").replace("⬜", "0"))
    guesses = re.findall("([012]{5})", text)
    return guesses


def make_freqs():
    df = pd.read_csv("unigram_freq.csv")
    # Establish a minimum frequency for any Wordle word that's missing from the frequency dataset
    min_freq = 0
    english_freqs = {df["word"][i]: df["count"][i] for i in df.index}
    return {
        w: min_freq if w not in english_freqs else english_freqs[w]
        for w in short_words
    }


def stringify(x):
    return ''.join(str(y) for y in x)


def process_result(r, target_words):
    target = r[0]['target']
    temp_list = [
        stringify(x['score']) for x in r if x['guess'] in target_words
    ]
    #  freq_list = [glove_rank_dict.get()]
    return {target: Counter(temp_list)}


def get_num_line(guess, answer):
    """Make the wordle score line for a given guess and answer, method borrowed from my Wordle solver class"""
    match_and_position = [
        2 * int(letter == answer[i]) for i, letter in enumerate(guess)
    ]
    remaining_letters = [
        x for i, x in enumerate(answer) if match_and_position[i] != 2
    ]

    # print('remaining letters', remaining_letters)

    def find_non_position_match(remaining_letters, guess):
        """has to be a better way"""
        res = []
        for i, letter in enumerate(guess):
            # print(letter)
            # print(letter in remaining_letters)
            if letter in remaining_letters and match_and_position[i] != 2:
                res.append(1)
                remaining_letters.remove(letter)
            else:
                res.append(0)
        return res

    non_position_match = find_non_position_match(remaining_letters, guess)
    return [x or y for x, y in zip(match_and_position, non_position_match)]


def process_result2(r, freqs=None):
    temp_list = [{
        'str_score': stringify(x['score']),
        'guess': x['guess']
    } for x in r]
    df = pd.DataFrame(temp_list)
    df['guess_rank'] = df['guess'].apply(lambda x: freqs.get(x, 0))
    out = df.groupby('str_score')['guess_rank'].sum()
    return out.to_dict()


def helper_func(target_word, freqs):
    return process_result2([{
        'score': get_num_line(x, target_word),
        'target': target_word,
        'guess': x
    } for x in short_words], freqs)


def flatten_columns(self):
    """Monkey patchable function onto pandas dataframes to flatten multiindex column names from tuples. Especially useful
    with plotly.
    pd.DataFrame.flatten_columns = flatten_columns
    """
    df = self.copy()
    df.columns = [
        '_'.join([str(x)
                  for x in [y for y in item
                            if y]]) if not isinstance(item, str) else item
        for item in df.columns
    ]
    return df
