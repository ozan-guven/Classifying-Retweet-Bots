from encodings import utf_8
from typing import Generator, Tuple
import pandas as pd
import numpy as np
import twarc
import config
import json
import bz2
import csv
import os

FIELD_NAMES = ['author_id', 'lang', 'rt_ratio', 'num_tweet']
FILE_NAME = "outputs/done.csv"

twarc2 = twarc.Twarc2(bearer_token=config.BEARER_TOKEN, metadata=False)

df = pd.read_csv("outputs/authors_langs_ratio.csv", usecols=['author_id', 'lang'])

english = df[df['lang'] == 'en'].to_numpy()
french = df[df['lang'] == 'fr'].to_numpy()
turkish = df[df['lang'] == 'tr'].to_numpy()
#print(turkish[9][0])


def check_200_tweets(author_ids: int) -> bool:
    """
        Given the author_id, checks if this user has 200 tweets or not.
    """
    gen: Generator[dict] = twarc2.user_lookup(author_ids)
    for data in gen:
        if 'data' in data:
            datas: dict = data['data'][0]  # Get the first JSON data
            public_metrics = datas['public_metrics'] 
            print(public_metrics)
            return 'public_metrics' in datas and datas['public_metrics']['tweet_count'] >= 200
        else:
            return False


def get_timeline(author_id: int, lang: str, iter: int) -> Tuple[int, int]:
    """Get the last 200 tweets for a given user and returns the next_token

    Args:
        author_id (int): id of the user

    Returns:
        Tuple[int, int]: the number of tweets got from the timeline and the number of rewteets in them
    """
    meta: dict = {}
    num_tweet = 0 # number of collected tweets
    num_rt = 0  # number of retweets
    with bz2.open("outputs/"+lang+"/" + str(author_id) + ".jsonl.bz2", "a") as f:
        # Check if user has 200 tweets
        if not check_200_tweets([author_id]):
            return (num_tweet, num_rt)
        
        gen = twarc2.timeline(author_id, max_results=100)
        for datas in gen:
            tweets: list[dict] = datas['data'] # retruns a list of dict of tweets
            meta = datas['meta']
            for tweet in tweets:
                print(f"iter: {iter} ; lang: {lang} tweet: {num_tweet}")
                f.write(bytes(json.dumps(tweet)+"\n", "UTF-8"))
                if "referenced_tweets" in tweet and tweet["referenced_tweets"][0]["type"] == "retweeted":
                    num_rt += 1
                num_tweet += 1
                if num_tweet >= 200:
                    return (num_tweet, num_rt)
        return (num_tweet, num_rt)

    

with open(FILE_NAME, "a", newline='') as file:
    csv_writer = csv.writer(file)
    #csv_writer.writerow(FIELD_NAMES)

    for i in range(3000, 3333):
        num_tweet, num_rt = get_timeline(int(english[i][0]), "en", i)
        if num_tweet < 1:
            os.remove("outputs/en/" + str(english[i][0]) + ".jsonl.bz2")
        else:
            csv_writer.writerow([english[i][0], "en", num_rt/num_tweet, num_tweet])

        num_tweet, num_rt = get_timeline(int(french[i][0]), "fr", i)
        if num_tweet < 1:
            os.remove("outputs/fr/" + str(french[i][0]) + ".jsonl.bz2")
        else:
            csv_writer.writerow([french[i][0], "fr", num_rt/num_tweet, num_tweet])
        
        num_tweet, num_rt = get_timeline(int(turkish[i][0]), "tr", i)
        if num_tweet < 1:
            os.remove("outputs/tr/" + str(turkish[i][0]) + ".jsonl.bz2")
        else:
            csv_writer.writerow([turkish[i][0], "tr", num_rt/num_tweet, num_tweet])

