# Wordle inferred from Twitter shared results.

This repository started exclusively as an effort to 'solve' the daily wordle with only shared scores on Twitter. However, I have also analyzed the [Most Popular Wordle Openers Analysis](https://marcoshuerta.com/wordle_openers/) using Twitter data.

### The Notebooks: 

More details on Solving Wordle with tweets in the Jupyter Notetbooks:

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)

### Discussion

The `TwitterWordle` class here can predict the wordle of the day only from public tweets. This is an alternative and maybe a little simpler approach than this excellent [Ben Hamner's Kaggle project](https://www.kaggle.com/benhamner/wordle-1-6).

I can't decide if this is the coolest way to "solve" wordle or the dumbest. I do think it's a fun problem to try and extract a signal from what seems like noisy data.

The code now, by default, runs in a mode where it doesn't reveal the answer, it should print a SHA256 hash of the answer and compare it to a hashed answer dictionary to verify if it's correct (assuming the NY Times doesn't change the deterministic pre-shuffled order.) Similarly the plot, by default, will has the words on the x-axis.

Storing tweets is [complicated](https://developer.twitter.com/en/developer-terms/agreement-and-policy), so best to [download the data from kaggle](https://www.kaggle.com/benhamner/wordle-tweets), I'm not hosting any tweets in this repository. I have a helper function that uses [searchtweets](https://pypi.org/project/searchtweets-v2/) to download, if you have a Developer account and API keys.

Major differences from above Kaggle notebook:

* **No simulations of hypothetical games.** I do use a similar word commonality lookup dictionary, and the same [word frequency data](https://www.kaggle.com/rtatman/english-word-frequency).
* **No cosine similarity or comparison of specific (e.g. penultimate) guess.** Only the list, and to some extent count, of all tweeted wordle score lines is needed.
* **Slightly different filtering of bad tweets** Upon further reflection, the code now rejects obviously bad tweets. The kaggle data set does some [light filtering](https://www.kaggle.com/benhamner/pull-wordle-tweets). In general, using a minimum count threshold mostly eliminates a few fake or spurious scores that were posted, and the penalty term is small enough that even if the data set has a bunch of retweets of a [tetris pattern](https://twitter.com/TomWritesBlog/status/1489676441562361858), the algorithm still converged accurately. However, non-English wordles or people tweeting out multiple variants at once are both easy to detect so I'm [now removing these](https://github.com/astrowonk/TwitterWordle/commit/98ee732bf50d896e007c01520a95e90dc4edd4a7).
* **100% Accuracy** This algorithm has 100% accuracy from Wordles 210-233 (the original project initially failed on 223, it was successful on later [reruns after some fixes](https://twitter.com/benhamner/status/1489364155370926080). It also failed on 231,236,and 249.) With the restricted target list, `TwitterWordle` is 100% accurate (so far).
  * _Note: Starting on Feb 15, the NY Times removed a few target words from the official wordle list, such as 'papal' and 'agora.' Some people continue to tweet results from the unaltered list, presumably cached/saved versions. So, on Wordle 247, using the full 12,000+ dictionary, `TwitterWordle` did fail to solve correctly. However, the default mode is using the smaller target dictionary._
* **By default, the code only considers the known 2315 possible wordles.** The Kaggle project doesn't give the wordle list special treatment, and runs simulations considering all 12K words as possible answers. While my [wordlebot](https://github.com/astrowonk/wordle) has rolled its own dictionary, I used the actual wordle list here. 
  * Use the keyword argument `use_limited_targets = False` to load precomputed dictionaries across the full 12972 word list, and the `Create Lookup dictionary` notebook can generate this larger set of dictionaries.
  * The code still solves with (almost, see above) 100% accuracy using all 12K+ words, I solve the dataframe using the full list in this notebook at the end.
  * As of Feb 15, 2021 I now use a revised dictionary after [changes made by the New York Times](https://arstechnica.com/gaming/2022/02/heres-how-the-new-york-times-changed-wordle/).

The `solve` method of the main class returns an image of the top candidate scores, here is Wordle 223:

![perky](https://user-images.githubusercontent.com/13702392/152341488-e80362a7-6d34-469f-97e1-094de1a14a25.png)

### The Notebooks: 

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)
