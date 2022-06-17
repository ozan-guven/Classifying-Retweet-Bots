from typing import Generator
import twarc
import config
import pandas as pd
import bz2
import json
import csv

users = 'new_outputs/users_20220601.jsonl'
ratio = 'new_outputs/user_ratio_20220601.csv'

FIELD_NAMES = ['author_id', 'rt_ratio', 'num_tweet']

twarc2 = twarc.Twarc2(bearer_token=config.BEARER_TOKEN, metadata=False)

samples = twarc2.sample()

def get_last_200_tweets(uid: int) -> int:
    num_tweet = 0 # number of collected tweets
    num_rt = 0    # number of retweets
    with bz2.open("user_tweets/" + str(uid) + ".jsonl.bz2", "a") as f:
        
        gen = twarc2.timeline(uid, max_results=100)
        for datas in gen:
            tweets: list[dict] = datas['data'] # retruns a list of dict of tweets
            for tweet in tweets:
                f.write(bytes(json.dumps(tweet)+"\n", "UTF-8"))
                if "referenced_tweets" in tweet and tweet["referenced_tweets"][0]["type"] == "retweeted":
                    num_rt += 1
                num_tweet += 1
                if num_tweet >= 200:
                    return (num_tweet, num_rt)
        return (num_tweet, num_rt)

# Open the file where users will be written
with open(users, 'a', encoding='UTF-8') as f, open(ratio, 'a', newline='') as p:
    iteration = 0                       # Can be changed as needed
    csv_writer = csv.writer(p)
    csv_writer.writerow(FIELD_NAMES)    # Should be commented if the file has already been created with a header

    visited_ids = []

    # These lines are useful to create further samplings and not sample existing IDs.
    
    # df = pd.read_csv('outputs/done3.csv')
    # existing_ids = df['author_id'].to_numpy(dtype=str)
    # # Add existing ids to the visited ids list
    # visited_ids.extend(existing_ids)

    # df = pd.read_csv('new_outputs/user_ratio.csv')
    # existing_ids = df['author_id'].to_numpy(dtype=str)
    # # Add existing ids to the visited ids list
    # visited_ids.extend(existing_ids)

    for dict in samples:
        # Get only user infor
        users = dict['includes']['users']
        for user in users:
            user_id = user['id']
            # Check if public_metrics field is there
            if str(user_id) not in visited_ids and 'public_metrics' in user and user['public_metrics']['tweet_count'] >= 200:
                # Add the user id the list of visited users
                visited_ids.append(str(user_id))

                # Add its user profile to the file
                f.write(f"{user}\n")

                # Get the last 200 tweets and compute the RT rate of the user
                num_tweet, num_rt = get_last_200_tweets(user_id)
                rate = 0
                if num_tweet > 0:
                    rate = num_rt/num_tweet
                csv_writer.writerow([user_id, rate, num_tweet])
                
                print(f'Iteration {iteration}, rt_rate : {rate}')
                
                iteration += 1
                if iteration >= 10_000:
                    # If 10_000 users, exit program
                    exit(0)


# Two examples of sampled users

# {'created_at': '2011-11-18T01:54:20.000Z', 'description': '♉︎ // M❥', 'entities': 
# {'url': {'urls': [{'start': 0, 'end': 23, 'url': 'https://t.co/eHmAYnRv1E', 'expanded_url': 'https://instagram.com/ashdenisep?r=nametag',
#  'display_url': 'instagram.com/ashdenisep?r=n…'}]}},
#  'id': '415216158', 'location': 'North Carolina', 'name': '𝔸𝕤𝕙',
#  'profile_image_url': 'https://pbs.twimg.com/profile_images/1487551413244809218/xzslXRdv_normal.jpg',
#  'protected': False, 'public_metrics': {'followers_count': 454, 'following_count': 93, 'tweet_count': 30979, 'listed_count': 0}, 'url': 'https://t.co/eHmAYnRv1E', 
# 'username': 'ashleydenisep', 'verified': False}

# {'verified': False, 'protected': False,
#  'entities': {'description': {'mentions': [{'start': 25, 'end': 40, 'username': 'ohenepilatoba_'}, {'start': 57, 'end': 67, 'username': 'ChelseaFc'},
#  {'start': 75, 'end': 88, 'username': 'KWESIARTHUR_'},
#  {'start': 93, 'end': 108, 'username': 'iamkingpromise'}, {'start': 134, 'end': 144, 'username': 'ChelseaFc'}]}}, 
# 'url': '', 'location': 'Kumasi, Ghana', 
# 'description': 'FOLLOW MY BACKUP ACCOUNT @ohenepilatoba_\nHardcore fan of @ChelseaFc\nI LOVE @KWESIARTHUR_ and @iamkingpromise\nINFLUENCER|| 
# I SUPPORTS  @ChelseaFc||', 'id': '1426239436011057152', 
# 'public_metrics': {'followers_count': 2761, 'following_count': 2132, 'tweet_count': 16114, 'listed_count': 1},
#  'created_at': '2021-08-13T17:49:26.000Z', 'profile_image_url': 'https://pbs.twimg.com/profile_images/1490126456449601537/PPl_TWZ1_normal.jpg',
#  'name': 'OHENE PILATO𓃵', 'pinned_tweet_id': '1474669131295342593', 'username': 'carter___1'}
