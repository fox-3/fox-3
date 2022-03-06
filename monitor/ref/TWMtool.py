# TwitterAPIを活用しやすくするため、独自に作ったクラス及びメソッド
# monitor.pyにて活用
# requestsで直接TwitterAPIにリクエストするメソッドと、Tweepyを用いてリクエストするメソッド両方含む。

import os, tweepy, requests, json, csv, requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2
from datetime import datetime

dirname = os.path.dirname(__file__)
os.chdir(dirname)
load_dotenv("env")

class TWP:
    def __init__(self):
        self.APIkey = os.getenv("APIkey")
        self.APIkeyS = os.getenv("APIkeyS")
        self.BearerToken = os.getenv("BearerToken")
        self.AccessToken = os.getenv("AccessToken")
        self.AccessTokenS = os.getenv("AccessTokenSecret")
        #self.url = url
        self.params = {}
        self.header= {"Authorization": "Bearer {}".format(self.BearerToken)}
        self.client = tweepy.Client(bearer_token=os.getenv("BearerToken"), 
                                    consumer_key=os.getenv("APIkey"), 
                                    consumer_secret=os.getenv("APIkeyS"), 
                                    access_token=os.getenv("AccessToken"), 
                                    access_token_secret=os.getenv("AccessTokenSecret"))
        self.auth1 = OAuth1(self.APIkey, self.APIkeyS, self.AccessToken, self.AccessTokenS)

    def userLKUP(self, Name):
        return self.client.get_user(username=Name)[0]["id"]

    def twi1(self, url, params):
        r = requests.get(url, params ,auth= OAuth1(self.APIkey, self.APIkeyS, self.AccessToken, self.AccessTokenS))
        print()
        return r.json()