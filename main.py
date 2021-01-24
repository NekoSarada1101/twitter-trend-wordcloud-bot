import json
import os
import urllib
import emoji
import requests
from google.cloud import language_v1, storage
from wordcloud import WordCloud
from requests_oauthlib import OAuth1Session
from setting_secret import *

language_client = language_v1.LanguageServiceClient.from_service_account_file("credentials.json")
storage_client = storage.Client.from_service_account_json("credentials.json")
bucket = storage_client.get_bucket('slack_bot_storage')
twitter = OAuth1Session(CK, CS, AT, AS)


def main(data, context):
    trend_noun_list = extract_noun(remove_emoji(keyword))  # type: list

    noun_list = []  # type: list
    for index in range(len(tweet_list)):
        text = remove_emoji(tweet_list[index]["text"])  # type: str
        # 名詞を抽出
        noun_list.extend(extract_noun(text))
    print("nouns={}".format(len(noun_list)))

    create_word_cloud(noun_list, keyword, trend_noun_list)
    post_tweet(keyword)
    trend_word = fetch_trend_top()  # type: str
    tweet_list = fetch_tweet_list(trend_word)  # type: list


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


def extract_noun(text: str) -> list:
    noun_list = []  # type: list
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    syntax = language_client.analyze_syntax(request={'document': document})  # type: json
    for token in syntax.tokens:
        part_of_speech = token.part_of_speech  # type: json
        if language_v1.PartOfSpeech.Tag(part_of_speech.tag).name == "NOUN":  # もし名詞なら
            noun_list.append(token.text.content)
    return noun_list


def create_word_cloud(noun_list: list, keyword: str, trend_noun_list: list):
    download_font_file()

    font_path = "/tmp/ヒラギノ角ゴシック W3.ttc"  # type : str
    stop_words = ["RT", "@", ":/", 'もの', 'こと', 'とき', 'そう', 'たち', 'これ', 'よう', 'これら', 'それ', 'すべて', 'https',
                  keyword]  # type: list
    stop_words.extend(trend_noun_list)
    word_chain = ' '.join(noun_list)
    word_cloud = WordCloud(background_color="white", font_path=font_path, contour_color='steelblue', collocations=False,
                           contour_width=3, width=900, height=500, stopwords=set(stop_words)).generate(word_chain)
    word_cloud.to_file("/tmp/wc_image_ja.png")


def download_font_file():
    if os.path.exists('/tmp/ヒラギノ角ゴシック W3.ttc') is False:
        print("Download FontFile")
        try:
            # GCSにあるダウンロードしたいファイルを指定
            blob = bucket.blob("ヒラギノ角ゴシック W3.ttc")
            # ファイルとしてローカルに落とす
            blob.download_to_filename("/tmp/ヒラギノ角ゴシック W3.ttc")
        except Exception as exception:
            print(exception)


def post_tweet(keyword: str):
    endpoint_url = "https://upload.twitter.com/1.1/media/upload.json"  # type: str
    files = {  # type: dict
        "media": open('/tmp/wc_image_ja.png', 'rb')
    }
    response = twitter.post(url=endpoint_url, files=files)  # type: response
    media_id = json.loads(response.text)['media_id']  # type: str

    endpoint_url = "https://api.twitter.com/1.1/statuses/update.json"  # type: str
    # Media ID を付加してテキストを投稿
    params = {'status': "{}\nのWordCloud".format(keyword), "media_ids": [media_id]}  # type: dict
    response = twitter.post(url=endpoint_url, params=params)  # type: response
    print("post_response\n{}".format(json.loads(response.text)))


if __name__ == '__main__':
    main()
