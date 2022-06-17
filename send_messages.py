import tweepy
import config

auth = tweepy.OAuthHandler(consumer_key=config.CONSUMER_KEY, consumer_secret=config.CONSUMER_SECRET)
auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_SECRET)
api = tweepy.API(auth)
print(auth.username)
1316762595525877760
options = [
            {
              "label": "Yes",
              "description": "Yes I am a bot.",
              "metadata": "external_id_1"
            },
            {
              "label": "No",
              "description": "No I am not a bot.",
              "metadata": "external_id_2"
            }
         ]
tugrul_id = 1480636633
mine = 1316762595525877760
api.send_direct_message(tugrul_id, "This is a test.")
