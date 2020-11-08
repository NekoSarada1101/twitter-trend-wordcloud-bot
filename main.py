import json
import requests
from requests_oauthlib import OAuth1Session
from setting_secret import *

def main():
    keyword = fetch_trend_top()  # type: str
    tweet_list = fetch_tweet_list(keyword)  # type: list


def fetch_trend_top() -> str:
    endpoint_url = "https://api.twitter.com/1.1/trends/place.json?id=23424856"  # type: str
    header = {  # type: dict
        "Authorization": "Bearer " + BEARER_KEY
    }
    response = requests.get(url=endpoint_url, headers=header)  # type: response
    top_trend = json.loads(response.text)[0]["trends"][0]["name"]  # type: str
    return top_trend


def fetch_tweet_list(keyword: str) -> list:
    keyword = urllib.parse.quote(keyword)  # type: str
    max_results = 100  # type: int
    endpoint_url = "https://api.twitter.com/2/tweets/search/recent?query={}&max_results={}".format(keyword, str(
        max_results))  # type: str
    header = {  # type: dict
        "Authorization": "Bearer " + BEARER_KEY
    }
    response = requests.get(url=endpoint_url, headers=header)  # type: response
    tweet_list = json.loads(response.text)["data"]  # type: list
    return tweet_list