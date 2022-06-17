from typing import Generator
import twarc
import config

twarc2 = twarc.Twarc2(bearer_token=config.BEARER_TOKEN, metadata=False)

def check_200_tweets(author_ids: int) -> bool:
    """
        Given the author_id, checks if this user has 200 tweets or not.
    """
    gen: Generator[dict] = twarc2.user_lookup(author_ids)
    for data in gen:
        print(data)
        if 'data' in data:
            datas: dict = data['data'][0]  # Get the first JSON data
            public_metrics = datas['public_metrics'] 
            print(public_metrics)
            return 'public_metrics' in datas and datas['public_metrics']['tweet_count'] >= 200
        else:
            return False

check_200_tweets([1495998858387943426])

"""
User example:
{'data': [{'protected': False, 'description': '', 'created_at': '2022-02-22T05:48:33.000Z', 'username': 'DawnJon26077024', 'name': 'Dawn Jones', 'id': '1495998858387943426', 'url': '', 'verified': False, 'profile_image_url': 'https://pbs.twimg.com/profile_images/1495999012130148352/Es7Feofx_normal.jpg', 'public_metrics': {'followers_count': 3, 'following_count': 0, 'tweet_count': 1775, 'listed_count': 0}}]}
"""