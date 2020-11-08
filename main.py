import json
import requests
from setting_secret import *

def main():
    keyword = fetch_trend_top()  # type: str


def fetch_trend_top() -> str:
    endpoint_url = "https://api.twitter.com/1.1/trends/place.json?id=23424856"  # type: str
    header = {  # type: dict
        "Authorization": "Bearer " + BEARER_KEY
    }
    response = requests.get(url=endpoint_url, headers=header)  # type: response
    top_trend = json.loads(response.text)[0]["trends"][0]["name"]  # type: str
    return top_trend