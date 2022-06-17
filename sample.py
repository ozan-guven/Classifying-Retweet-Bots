# This is used to generate random sample tweets and save them in a JSON file

import json
import csv
import twarc
import tweepy
import config

MAX_USER_PER_LANG = 10_000
FIELD_NAMES = ['author_id', 'lang', 'rt_ratio']
FILE_NAME = "outputs/authors_langs_ratio.csv"

class Sampler(tweepy.StreamingClient):
    def __init__(self, writer, bearer_token):
        # Debug counter
        # self.counter = 0 
        self.num_match = {'fr': 6684, 'en': 10000, 'tr': 10000}#{"fr": 0, "en": 0, "tr": 0}
        """ Field represents the number of current author_ids per language that have been scanned """

        self.ids: dict[int, str] = {}
        """ Dictionnary that contains the author_id as keys and the pair of their language """

        self.writer = writer

        tweepy.StreamingClient.__init__(self, bearer_token=bearer_token)

    def check_lang(self, tweet: tweepy.Tweet) -> bool:
        """
            Checks if the given tweet has a language field set to English, French or Turkish
            and checks if the maximum number of users per language is not reached
        """
        
        lang: str = tweet.lang
        correct_lang = lang is not None and (lang == "fr" or lang == "en" or lang == "tr")

        if correct_lang and self.num_match[lang] < MAX_USER_PER_LANG:
            # Increment the number of users in dictionary
            self.num_match[lang] = self.num_match[lang] + 1
            return True
        else:
            return False

    def is_retweet(self, tweet: tweepy.Tweet) -> bool:
        """
            Checks if a recieved tweet has the referenced_tweets field
            and if so checks if the type of the reference is a retweet
        """
        return tweet.referenced_tweets is not None and tweet.referenced_tweets.pop().type == "retweeted"

    def on_tweet(self, tweet: tweepy.Tweet):
        
        # Check if the given tweet corresponds to the requirements
        if self.is_retweet(tweet):
            id = tweet.author_id
            if id is not None and id not in self.ids and self.check_lang(tweet):
                print(self.num_match)
                self.ids[id] = tweet.lang
                self.writer.writerow([id, tweet.lang, 0.0])
        
        # self.counter += 1
        if self.num_match['fr'] >= MAX_USER_PER_LANG and self.num_match['en'] >= MAX_USER_PER_LANG and self.num_match['tr'] >= MAX_USER_PER_LANG:
            exit(0)

# Instanciate the Sampler class and begins sampling
with open(FILE_NAME, "w", newline='') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerow(FIELD_NAMES)

    sampler = Sampler(writer=csv_writer, bearer_token=config.BEARER_TOKEN)
    sampler.sample(expansions=["author_id", "referenced_tweets.id"], tweet_fields="lang")

# t = twarc.client2.Twarc2(bearer_token=config.BEARER_TOKEN)
# tweets = t.sample()
# with open("sample2.json", "w") as f:
#     for tweet in tweets:
#         print(tweet)
#         f.write(json.dumps(tweet)+"\n")

