# Wordle inferred from Twitter shared results.

### The Notebooks: 

More details in the Jupyter Notetbooks:

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)

### Discussion

One can predict the wordle of the day only from public tweets. This is an alternative and maybe a little simpler approach than this excellent [Kaggle project](https://www.kaggle.com/benhamner/wordle-1-6).

I can't decide if this is the coolest way to "solve" wordle or the dumbest. Obviously it's sort of cheating, but it's cheating with statistics in a neat way. I think it's pretty cool it works.

Storing tweets is [complicated](https://developer.twitter.com/en/developer-terms/agreement-and-policy), so best to [download the data from kaggle](https://www.kaggle.com/benhamner/wordle-tweets), I'm not hosting any tweets here. I have a helper function that uses [searchtweets](https://pypi.org/project/searchtweets-v2/) to download, if you have a Developer account and API keys.

Major differences from above Kaggle notebook:

* **No simulations of hypothetical games.** I do use a similar word commonality lookup dictionary.
* **No cosine similarity or comparison of specific (e.g. penultimate) guess.** Only the list, and to some extent count, of all tweeted wordle score lines is needed.
* **No explicit filtering of spurious tweets.** The kaggle data set does some [light filtering](https://www.kaggle.com/benhamner/pull-wordle-tweets), however when I collect them myself, I do no pre-processing. For large N of tweets, a min-count threshold is used to remove false or impossible line scores. For small N, the penalty term is small enough that 1 or 2 false lines won't impact the final result. I suppose the risk is someone who might put the results for several wordles in one tweet, but so far it hasn't been an issue.
* **100% Accuracy** This algorithm has 100% accuracy from Wordles 210-228.

The `solve` method of the main class returns an image of the top candidate scores, here is Wordle 223:

![perky](https://user-images.githubusercontent.com/13702392/152341488-e80362a7-6d34-469f-97e1-094de1a14a25.png)

### The Notebooks: 

[Predict from Tweets](Predict%20with%20Tweets.ipynb)

[Create Lookup Dictionaries](Create%20Lookup%20dictionary.ipynb)
