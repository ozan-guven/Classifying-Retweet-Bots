from concurrent import futures
from typing import Union
from itertools import count
from typing import Tuple
import threading

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import sklearn
from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import scale
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import json
import ast

import datetime
from dateutil import parser

import re

import bz2

from profanity_check import predict, predict_prob
from better_profanity import profanity

import string
import emoji

import itertools
from difflib import SequenceMatcher
import jellyfish

# There is no list of all available languages on Twitter :( https://developer.twitter.com/en/docs/twitter-for-websites/supported-languages, https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet)
lang_list = ['hy', 'si', 'dv', 'bo', 'pt', 'fa', 'ru', 'lo', 'eu', 'lv', 'th', 'pl', 'da', 'ro', 'bg', 'in', 'pa', 'tr', 'ja', 'und', 'cy', 'iw', 'no', 'or', 'ar', 'hu', 'nl', 'sl', 'it', 'mr', 'fr', 'cs', 'gu', 'es', 'ps', 'sv', 'ko', 'de', 'fi', 'ne', 'tl', 'el', 'kn', 'km', 'am', 'bn', 'my', 'ht', 'ckb', 'ur', 'vi', 'ta', 'sd', 'sr', 'hi', 'en', 'uk', 'te', 'ml', 'zh', 'ca', 'et', 'is', 'lt', 'ka']
annotation_types = ["Person", "Place", "Product", "Organization", "Other"]
existing_set = set(pd.read_csv("new_outputs/user_ratio_20220601.csv", dtype=str)["author_id"].to_numpy(dtype=str))#{"0"}

def create_feature(ratio_user_date_json: Tuple[list, str, datetime.datetime]):
    lines, user, date = ratio_user_date_json
    uid = int(lines[0])
    ratio = float(lines[1])
    num_tweets = int(lines[2])
    if num_tweets >= 200 and str(uid) not in existing_set:
        user = ast.literal_eval(user)
        if user["id"] != lines[0]:
            raise Exception("ERROR, not the same UID")
        if user["id"] in existing_set:
            return None

        # Create the features for a user
        user_features = {}

        # Feature 1. Number of days since account creation (i.e. date of creation)
        date_created = parser.parse(user["created_at"]).replace(tzinfo=None)
        date_streamed = date
        # Get the number of days since creation
        num_days = (date_streamed - date_created).days

        user_features["days_since_creation"] = num_days if num_days > 0 else 0

        # Default to 1 for all divisions
        if num_days < 1:
            num_days = 1

        # Feature 2. Retweet ratio
        user_features["rt_ratio"] = ratio

        ### USER ITSELF

        # Feature username
        # Length of username
        username: str = user["username"]
        username_length = len(username)
        
        user_features["length_username"] = username_length
        
        username_letters = sum(c.isalpha() for c in username)
        username_digits = sum(c.isdigit() for c in username)
        # Number of letters
        user_features["letters_in_username"] = username_letters
        # Number of numbers
        user_features["numbers_in_username"] = username_digits
        # Non numeric or letters
        user_features["special_chars_in_username"] = username_length - username_letters - username_digits

        # Feature 3. has a profile picture
        default_pp_url = "https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png"
        user_features["has_profile_image"] = int(user["profile_image_url"] != default_pp_url)

        # Feature 4. protected
        user_features["is_protected"] = int(user["protected"])

        ### PUBLIC METRICS
        # Feature 5. number of followers
        user_features["n_followers"] = user["public_metrics"]["followers_count"]
        # Feature 6. number of following accounts
        user_features["n_following"] = user["public_metrics"]["following_count"]
        # Feature 7. number of tweets
        user_features["n_tweets"] = user["public_metrics"]["tweet_count"]
        # Feature 8. number of lists
        user_features["n_lists"] = user["public_metrics"]["listed_count"]

        # Feature 8.1 following/followers rate
        user_features["followings_followers_rate"] = 0 if user_features["n_followers"] == 0 else user_features["n_following"] / user_features["n_followers"]

        # Feature 8.2 Followers/num_days: avg num of follower per day
        user_features["avg_num_followers_per_day"] = user["public_metrics"]["followers_count"] / num_days

        # Feature 8.3 Folowing/num_days: avg_num_of_following per day
        user_features["avg_num_followings_per_day"] = user["public_metrics"]["following_count"] / num_days

        # Feature 8.4 Tweet rate
        tweet_rate = user_features["n_tweets"] / num_days
        user_features["avg_num_tweets_per_day"] = tweet_rate

        # Feature 8.5 List rate
        user_features["avg_num_lists_per_day"] = user_features["n_lists"] / num_days

        ### SOCIAL MEDIAS

        # Feature 10. Has Instagram
        inst = False
        num_links = 0
        if "entities" in user and "url" in user["entities"] and "urls" in user["entities"]["url"]:
            for objs in user["entities"]["url"]["urls"]:
                num_links += 1
                inst |= "display_url" in objs and "instagram" in objs["display_url"].lower()
        elif "entities" in user and "description" in user["entities"] and "urls" in user["entities"]["description"]:
            for objs in user["entities"]["description"]["urls"]:
                num_links += 1
                inst |= "display_url" in objs and "instagram" in objs["display_url"].lower()
        
        reg = r"\s*(ig|insta(gram)?)(\s*:|\s)(\s|@|_)"
        regexp = re.compile(reg, re.IGNORECASE | re.UNICODE)
        if regexp.search(user["description"]):
            #count+=1
            #print(count, user["description"])
            inst |= True
        
        user_features["has_insta"] = int(inst)

        # Feature 11. Has Facebook
        face = False
        if "entities" in user and "url" in user["entities"] and "urls" in user["entities"]["url"]:
            for objs in user["entities"]["url"]["urls"]:
                face |= "display_url" in objs and "facebook" in objs["display_url"].lower()
        elif "entities" in user and "description" in user["entities"] and "urls" in user["entities"]["description"]:
            for objs in user["entities"]["description"]["urls"]:
                face |= "display_url" in objs and "facebook" in objs["display_url"].lower()
        
        reg = r"\s*(fb|facebook)(\s*:|\s)(\s|@|_)"
        regexp = re.compile(reg, re.IGNORECASE | re.UNICODE)
        if regexp.search(user["description"]):
            #count+=1
            #print(count, user["description"])
            face |= True
        
        user_features["has_facebook"] = int(face)

        # Feature 12. Has YouTube
        yt = False
        if "entities" in user and "url" in user["entities"] and "urls" in user["entities"]["url"]:
            for objs in user["entities"]["url"]["urls"]:
                yt |= "display_url" in objs and "youtube" in objs["display_url"].lower()
        elif "entities" in user and "description" in user["entities"] and "urls" in user["entities"]["description"]:
            for objs in user["entities"]["description"]["urls"]:
                yt |= "display_url" in objs and "youtube" in objs["display_url"].lower()
        
        reg = r"\s*(yt|youtube)(\s*:|\s)(\s|@|_)"
        regexp = re.compile(reg, re.IGNORECASE | re.UNICODE)
        if regexp.search(user["description"]):
            #count+=1
            #print(count, user["description"])
            yt |= True
        
        user_features["has_youtube"] = int(yt)

        # Feature 13. Has Snapchat
        snap = False
        if "entities" in user and "url" in user["entities"] and "urls" in user["entities"]["url"]:
            for objs in user["entities"]["url"]["urls"]:
                snap |= "display_url" in objs and "snapchat" in objs["display_url"].lower()
        elif "entities" in user and "description" in user["entities"] and "urls" in user["entities"]["description"]:
            for objs in user["entities"]["description"]["urls"]:
                snap |= "display_url" in objs and "youtube" in objs["display_url"].lower()
        
        reg = r"\s*(snap(chat)?)(\s*:|\s)(\s|@|_)"
        regexp = re.compile(reg, re.IGNORECASE | re.UNICODE)
        if regexp.search(user["description"]):
            #count+=1
            #print(count, user["description"])
            snap |= True
        
        user_features["has_snapchat"] = int(snap)

        ### VARIOUS COUNTS

        # Feature 14. Hashtag count in description
        ht = 0
        if "entities" in user and "description" in user["entities"] and "hashtags" in user["entities"]["description"]:
            ht = len(user["entities"]["description"]["hashtags"])
        
        user_features["hashtags_in_description"] = ht

        # Feature 14. Mention count in description
        ment = 0
        if "entities" in user and "description" in user["entities"] and "mentions" in user["entities"]["description"]:
            ment = len(user["entities"]["description"]["mentions"])
        
        user_features["mentions_in_description"] = ment

        # Feature 15. Number of links in profile
        user_features["links_in_profile"] = num_links

        ### VARIOUS BOOLEANS

        # Feature 16. Has description
        user_features["has_description"] = int(user["description"] != "")

        # Feature 16. Has location
        user_features["has_location"] = int("location" in user and user["location"] != "")

        # Feature 17. Is verified
        user_features["is_verified"] = int(user["verified"])

        # Feature 18. Has pinned tweet
        user_features["has_pinned_tweet"] = int("pinned_tweet_id" in user)

        # Analysis of description
        des: str = user["description"]
        user_features["length_description"] = len(des)
        
        des_letters = sum(c.isalpha() for c in des)
        des_digits = sum(c.isdigit() for c in des)
        des_spaces = sum(c.isspace() for c in des)
        # Number of letters
        user_features["letters_in_description"] = des_letters
        # Number of numbers
        user_features["numbers_in_description"] = des_digits
        # Number of spaces
        user_features["spaces_in_description"] = des_spaces
        # Number of non numeric or letters
        user_features["special_chars_in_description"] = username_length - username_letters - username_digits
        # Number of punctuation
        user_features["punctuations_in_description"] = sum(True for c in des if c in string.punctuation)
        # Number of words in description
        user_features["words_in_description"] = len(des.split())
        # Number of emojies in description
        user_features["emojis_in_description"] = emoji.emoji_count(des)

        ### INFO ON TWEETS
        with bz2.open(f"new_outputs/user_tweets/{uid}.jsonl.bz2", "rt", encoding="UTF-8") as compressed_tweets:
            NUM_DOMAINS = 176
            NUM_TWEETS = 200
            num_tweets_with_context = 0
            context_vector = np.zeros(NUM_DOMAINS, dtype=np.int64)
            langs = {lang : 0 for lang in lang_list}
            num_tweets_with_lang = 0
            num_tweets_with_media = 0
            num_total_media = 0
            num_polls = 0

            dates = []

            # Represents the number of each annotation that are above 0.5 confidence
            annotations = {an : 0 for an in annotation_types}

            num_cashtag = 0
            num_hashtag = 0
            num_mention = 0
            num_url = 0

            has_geo = False
            sensitives = 0

            num_rt = 0
            num_reply = 0
            num_likes = 0
            num_quotes = 0

            dict_rts = {"a": 0}
            reply_count = 0

            # Checks the number of tweets that uses profanity in them
            profanity_count = 0

            # Tweet words analysis
            
            # Tweet text length
            avg_tweets_length = []
            avg_num_letters = []
            avg_num_numbers = []
            avg_num_spaces = []
            avg_num_special_chars = []
            avg_num_punctuations = []
            avg_num_words = []
            avg_num_emojies = []

            # The avg num of unique words per tweet
            avg_num_unique_words = []
            num_unique_words_in_all_tweets = set()

            # List of all tweet texts
            tweet_text_list = []
            
            # Loop over each tweet of the user
            for tweet_s in compressed_tweets.readlines():
                tweet = json.loads(tweet_s)

                tweet_text_list.append(tweet["text"])

                # Tweet length
                tweet_text: str = tweet["text"]
                avg_tweets_length.append(len(tweet_text))

                letters = 0
                numbers = 0
                spaces = 0
                punctuations = 0
                emojies = 0

                # Iterate over all characters of a string to find the metrics
                for c in tweet_text:
                    letters += c.isalpha()
                    numbers += c.isdigit()
                    spaces += c.isspace()
                    punctuations += c in string.punctuation
                    emojies += emoji.emoji_count(c)

                avg_num_letters.append(letters)
                avg_num_numbers.append(numbers)
                avg_num_spaces.append(spaces)
                avg_num_special_chars.append(len(tweet_text) - letters - numbers - spaces)
                avg_num_punctuations.append(punctuations)

                wds = tweet_text.split()
                wds_set = set(wds)
                num_unique_words_in_all_tweets.update(wds_set)

                avg_num_unique_words.append(len(wds_set))

                avg_num_words.append(len(wds))
                avg_num_emojies.append(emojies)

                if (predict_prob([tweet["text"]])[0] > 0.5):# or profanity.contains_profanity(tweet["text"]):
                    profanity_count += 1

                if "referenced_tweets" in tweet:
                    for ls in tweet["referenced_tweets"]:
                        # Feature: Repeating RTs
                        if "type" in ls and ls["type"] == "retweeted":
                            tw_id = ls["id"]
                            if tw_id in dict_rts:
                                dict_rts[tw_id] += 1
                            else:
                                dict_rts[tw_id] = 1
                        # Feature: number of replies to other tweets
                        if "type" in ls and ls["type"] == "replied_to":
                            reply_count += 1


                # Feature: Context annotations, creates 175 features
                if "context_annotations" in tweet:
                    num_tweets_with_context += 1
                    for domains in tweet["context_annotations"]:
                        if "domain" in domains:
                            context_vector[int(domains["domain"]["id"])] += 1
                
                #entity

                #language
                if "lang" in tweet:
                    num_tweets_with_lang += 1
                    langs[tweet["lang"]] += 1

                # Media attachments
                if "attachments" in tweet:
                    if "media_keys" in tweet["attachments"]:
                        num_tweets_with_media += 1
                        num_total_media += len(tweet["attachments"]["media_keys"])
                    if "poll_ids" in tweet["attachments"]:
                        num_polls += 1

                # Time feature 
                d = parser.parse(tweet["created_at"]).replace(tzinfo=None)
                dates.append(pd.Timedelta(f"{d:%H}:{d:%M}:{d:%S}").total_seconds())

                # Entities
                if "entities" in tweet:
                    # Anotations:
                    if "annotations" in tweet["entities"]:
                        for ant in tweet["entities"]["annotations"]:
                            if ant["probability"] >= 0.5:
                                annotations[ant["type"]] += 1

                    # Cashtags:
                    if "cashtags" in tweet["entities"]:
                        num_cashtag += len(tweet["entities"]["cashtags"])

                    # Hashtags:
                    if "hashtags" in tweet["entities"]:
                        num_hashtag += len(tweet["entities"]["hashtags"])
                    
                    # Mentions:
                    if "mentions" in tweet["entities"]:
                        num_mention += len(tweet["entities"]["mentions"])
                    
                    # URLs
                    if "urls" in tweet["entities"]:
                        num_url += len(tweet["entities"]["urls"])
                
                # Has geo ?
                has_geo |= "geo" in tweet

                # Sensitives
                sensitives += int(tweet["possibly_sensitive"])

                ### PUBLIC METRICS
                pm = tweet["public_metrics"]

                num_rt += pm["retweet_count"]
                num_reply += pm["reply_count"]
                num_likes += pm["like_count"]
                num_quotes += pm["quote_count"]
            
            # Feature: Number of tweets containing media
            user_features["n_tweets_with_media"] = num_tweets_with_media

            # Feature: Number of total media
            user_features["n_media"] = num_total_media

            # Feature: Number of tweets with a poll
            user_features["n_tweets_with_poll"] = num_polls

            # Feature: Average time of the tweets in a day (in the range [0, 1[)
            user_features["average_tweet_time"] = (np.array(dates).sum() / 200) / (60*60*24)

            # Feature: Number of cashtags
            user_features["num_total_cashtags"] = num_cashtag

            # Feature: Number of hashtags
            user_features["num_total_hashtags"] = num_hashtag

            # Feature: Number of mentions
            user_features["num_total_mentions"] = num_mention

            # Feature: Number of URLs
            user_features["num_total_urls"] = num_url

            # Feature: Has geo in one of the tweets
            user_features["has_geo_in_one_tweet"] = int(has_geo)

            # Feature: Number of possibly sensitive tweets
            user_features["num_possibly_sensitive"] = sensitives

            # Feature: Annotations
            for (k, v) in annotations.items():
                user_features[f"annotation_{k}"] = v

            # Feature: Context annotations, creates 175 features
            for i in range(NUM_DOMAINS):
                user_features[f"context_domain_{i}"] = context_vector[i] / num_tweets_with_context if num_tweets_with_context != 0 else 0

            # Feature: Languages
            for (k, v) in langs.items():
                user_features[f"lang_{k}"] = v / num_tweets_with_lang if num_tweets_with_lang != 0 else 0

            # Features: Public metrics on tweets
            user_features["avg_rt_on_tweets"] = num_rt / 200
            user_features["avg_reply_on_tweets"] = num_reply / 200
            user_features["avg_like_on_tweets"] = num_likes / 200
            user_features["avg_quote_on_tweets"] = num_quotes / 200

            # This features shows the number of tweets that have been retweeted 2 times or more
            # For example if tweet with id 1001 has been retweeted 4 times by a user, this will add 4 to the counter
            repeated_tweets = 0
            for (_, v) in dict_rts.items():
                if v >= 2:
                    repeated_tweets += v
            user_features["repeated_tweets"] = repeated_tweets

            # Number of tweets the user replied to
            user_features["replied_to"] = reply_count

            user_features["profanity"] = profanity_count

            user_features["stream_date"] = date_streamed.strftime('%m/%d/%Y')
            #print(f"Prof count: {profanity_count}")

            # Text length analysis
            user_features["mean_tweet_length"] = np.array(avg_tweets_length).mean()
            user_features["mean_num_letters"] = np.array(avg_num_letters).mean()
            user_features["mean_num_numbers"] = np.array(avg_num_numbers).mean()
            user_features["mean_num_spaces"] = np.array(avg_num_spaces).mean()
            user_features["mean_num_special_chars"] = np.array(avg_num_special_chars).mean()
            user_features["mean_num_punctuations"] = np.array(avg_num_punctuations).mean()
            user_features["mean_num_words"] = np.array(avg_num_words).mean()
            user_features["mean_num_emojies"] = np.array(avg_num_emojies).mean()

            user_features["avg_num_unique_words"] = np.array(avg_num_unique_words).mean()
            user_features["num_unique_words_in_all_tweets"] = len(num_unique_words_in_all_tweets)

            # Analyze all tweet texts of the user
            pairs = itertools.combinations(tweet_text_list, 2)
            # n(n-1)/2 = 19900 pairs; for n = 200
            similarities_jw = []
            similarities_ld = []
            similarities_sm = []
            # Compute pairwise similarities between all tweets
            for s1, s2 in pairs:
                similarities_jw.append(jellyfish.jaro_winkler_similarity(s1, s2))
                similarities_ld.append(jellyfish.levenshtein_distance(s1, s2))
                similarities_sm.append(SequenceMatcher(None, s1, s2).ratio())
            
            user_features["mean_jaro_winkler_similarity"] = np.array(similarities_jw).mean()
            user_features["mean_levenshtein_distance"] = np.array(similarities_ld).mean()
            # longest contiguous matching subsequence
            user_features["mean_lcs"] = np.array(similarities_sm).mean()
            user_features["uid"] = str(user["id"])
        return user_features

def create():
    """
    Create the features for the given set of users.

    Returns:
        list: the list of user features
    """
    
    # Here is the part that needs to be modified in order to execute it properly
    users = "users.jsonl"                   # The file that points to the user json
    ratios = "user_ratio.csv"               # The file that points to the csv file ratios of those user
    date = datetime.datetime(2022, 4, 1)    # The date the users were streamed
    
    ls = []
    
    with open(users, "r", encoding="UTF-8") as f:
        
        df = pd.read_csv(ratios, dtype=str)
        count = 0
        dates = [date for _ in range(len(df))]
        
        with futures.ProcessPoolExecutor() as pool:
            for user_feature in pool.map(create_feature, zip(df.to_numpy(), f.readlines(), dates)):
                #print(user_feature)
                if user_feature != None:
                    ls.append(user_feature)
                count += 1
                print(count)
    return ls

if __name__ == "__main__":
    ls = create()
    df = pd.DataFrame(ls)
    # This line writes the users into a new csv file
    df.to_csv("user_features.csv", index=False)
