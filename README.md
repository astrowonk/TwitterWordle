# Wordle inferred from Twitter shared results.

### The Notebooks: 

More details in the Jupyter Notetbooks:

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)

### Discussion

The `TwitterWordle` class here can predict the wordle of the day only from public tweets. This is an alternative and maybe a little simpler approach than this excellent [Ben Hamner's Kaggle project](https://www.kaggle.com/benhamner/wordle-1-6).

I can't decide if this is the coolest way to "solve" wordle or the dumbest. Obviously don't use this to "play" wordle because that's not fun, but it's pretty neat one can infer the answer just for all the tweets out there.

Storing tweets is [complicated](https://developer.twitter.com/en/developer-terms/agreement-and-policy), so best to [download the data from kaggle](https://www.kaggle.com/benhamner/wordle-tweets), I'm not hosting any tweets in this repository. I have a helper function that uses [searchtweets](https://pypi.org/project/searchtweets-v2/) to download, if you have a Developer account and API keys.

Major differences from above Kaggle notebook:

* **No simulations of hypothetical games.** I do use a similar word commonality lookup dictionary, and the same [word frequency data](https://www.kaggle.com/rtatman/english-word-frequency).
* **No cosine similarity or comparison of specific (e.g. penultimate) guess.** Only the list, and to some extent count, of all tweeted wordle score lines is needed.
* **No explicit filtering of spurious tweets.** The kaggle data set does some [light filtering](https://www.kaggle.com/benhamner/pull-wordle-tweets), however when I collect them myself, I do not pre-process the search results from the Twitter API. A minimum count threshold mostly eliminates a few fake or spurious scores that were posted, and the penalty term is small enough that even if the data set has a bunch of retweets of a [tetris pattern](https://twitter.com/TomWritesBlog/status/1489676441562361858), the algorithm still converges accurately.
* **100% Accuracy** This algorithm has 100% accuracy from Wordles 210-228 (the original project initially failed on 223, it was successful on later [reruns after some fixes](https://twitter.com/benhamner/status/1489364155370926080))
* **By default, the code only considers the known 2315 possible wordles.** The Kaggle project doesn't give it special treatment, and runs simulations considering all 12K words as possible answers. While my [wordlebot](https://github.com/astrowonk/wordle) has rolled its own dictionary, I used the actual wordle list here. 
  * Use the keyword argument `use_limited_targets = False` to load precomputed dictionaries across the full 12972 word list, and the `Create Lookup dictionary` notebook can generate this larger set of dictionaries.
  * The code still solves with 100% accuracy using all 12K+ words, I solve the dataframe using the full list in this notebook at the end.
  * I may change this to the default mode.

The `solve` method of the main class returns an image of the top candidate scores, here is Wordle 223:

![perky](https://user-images.githubusercontent.com/13702392/152341488-e80362a7-6d34-469f-97e1-094de1a14a25.png)

### The Notebooks: 

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)
