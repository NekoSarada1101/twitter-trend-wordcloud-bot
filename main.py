import json
import urllib
import emoji
import requests
from google.cloud import language_v1, storage
from requests_oauthlib import OAuth1Session
from setting_secret import *

language_client = language_v1.LanguageServiceClient.from_service_account_file("credentials.json")
def main():
    keyword = fetch_trend_top()  # type: str
    tweet_list = fetch_tweet_list(keyword)  # type: list

    noun_list = []  # type: list

    for index in range(len(tweet_list)):
        text = remove_emoji(tweet_list[index]["text"])  # type: str
        # 名詞を抽出
        noun_list.extend(extract_noun(text))
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


def remove_emoji(src_str: str) -> str:
    return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)


def extract_noun(text: str) -> list:
    noun_list = []  # type: list
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    syntax = language_client.analyze_syntax(request={'document': document})  # type: json
    for token in syntax.tokens:
        part_of_speech = token.part_of_speech  # type: json
        if language_v1.PartOfSpeech.Tag(part_of_speech.tag).name == "NOUN":  # もし名詞なら
            noun_list.append(token.text.content)
    return noun_list