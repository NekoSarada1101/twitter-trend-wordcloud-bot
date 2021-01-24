import json
import urllib
import emoji
import requests
from google.cloud import language_v1
from wordcloud import WordCloud
from requests_oauthlib import OAuth1Session
from settings import *

language_client = language_v1.LanguageServiceClient.from_service_account_file("credentials.json")
twitter = OAuth1Session(CK, CS, AT, AS)


def main(data, context):
    trend_word = fetch_trend_top()  # type: str
    tweet_list = fetch_tweet_list(trend_word)  # type: list
    noun_list = extract_noun(tweet_list)  # type: list
    create_word_cloud(noun_list)
    post_tweet(trend_word)


def fetch_trend_top() -> str:
    endpoint_url = "https://api.twitter.com/1.1/trends/place.json?id=23424856"  # type: str
    header = {"Authorization": "Bearer " + BEARER_KEY}  # type: dict
    response = json.loads(requests.get(url=endpoint_url, headers=header).text)  # type: json
    top_trend = response[0]["trends"][0]["name"]  # type: str
    print(top_trend)
    return top_trend


def fetch_tweet_list(keyword: str) -> list:
    keyword = urllib.parse.quote(keyword)  # type: str
    max_results = "100"  # type: str
    header = {"Authorization": "Bearer " + BEARER_KEY}  # type: dict
    tweet_list = []  # type: list
    next_token = ""  # type: str
    for i in range(TWEET_COUNT):
        endpoint_url = "https://api.twitter.com/2/tweets/search/recent?query={}&max_results={}" \
            .format(keyword, max_results)  # type: str
        if i >= 1:
            endpoint_url = endpoint_url + "&next_token={}".format(next_token)
        response = json.loads(requests.get(url=endpoint_url, headers=header).text)  # type: json

        for data in response["data"]:
            tweet_list.append(data["text"])

        try:
            next_token = response["meta"]["next_token"]
        except KeyError:
            print(KeyError)

    print("fetch_tweet_list complete")
    return tweet_list


def remove_emoji(src_str: str) -> str:
    return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)


def extract_noun(text_list: list) -> list:
    noun_list = []  # type: list
    for text in text_list:
        text = remove_emoji(text)  # type: str
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
        syntax = language_client.analyze_syntax(request={'document': document})  # type: json

        for token in syntax.tokens:
            part_of_speech = token.part_of_speech  # type: json
            if language_v1.PartOfSpeech.Tag(part_of_speech.tag).name == "NOUN":  # もし名詞なら
                noun_list.append(token.text.content)

    print("extract_noun complete")
    return noun_list


def create_word_cloud(noun_list: list):
    font_path = "./font/ヒラギノ角ゴシック W3.ttc"  # type : str
    stop_words = ["RT", "@", ":/", 'もの', 'こと', 'とき', 'そう', 'たち', 'これ', 'よう', 'これら', 'それ', 'すべて',
                  'https']  # type: list
    word_chain = ' '.join(noun_list)
    word_cloud = WordCloud(background_color="white", font_path=font_path, contour_color='steelblue',
                           collocations=False,
                           contour_width=3, width=900, height=500,
                           stopwords=set(stop_words)).generate(word_chain)
    word_cloud.to_file("/tmp/wc_image_ja.png")
    print("create_word_cloud complete")


def post_tweet(keyword: str):
    endpoint_url = "https://upload.twitter.com/1.1/media/upload.json"  # type: str
    files = {"media": open('/tmp/wc_image_ja.png', 'rb')}  # type: dict
    response = twitter.post(url=endpoint_url, files=files)
    media_id = json.loads(response.text)['media_id']  # type: str

    endpoint_url = "https://api.twitter.com/1.1/statuses/update.json"  # type: str
    # Media ID を付加してテキストを投稿
    params = {'status': "{}\nのWordCloud".format(keyword), "media_ids": [media_id]}  # type: dict
    response = twitter.post(url=endpoint_url, params=params)  # type: response
    print(response)


if __name__ == '__main__':
    main("data", "context")
