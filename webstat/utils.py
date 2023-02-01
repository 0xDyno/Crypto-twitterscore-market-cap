from time import sleep

import requests
from bs4 import BeautifulSoup


def convert_price(price) -> str:
    """
    Converts a price to a string.
    :param price: The price to convert.
    :return: The price as a string.
    """
    # Luckily it's written by TabninePro...
    if price < 0.000000001:
        return f"{price:.10f}"
    elif price < 0.00000001:
        return f"{price:.9f}"
    elif price < 0.0000001:
        return f"{price:.8f}"
    elif price < 0.000001:
        return f"{price:.7f}"
    elif price < 0.00001:
        return f"{price:.6f}"
    elif price < 0.0001:
        return f"{price:.5f}"
    elif price < 0.001:
        return f"{price:.4f}"
    elif price < 0.01:
        return f"{price:.3f}"
    elif price < 0.1:
        return f"{price:.2f}"
    else:
        return str(price)
    
    
def get_data_from_dicts(data, *args, index=0):
    """
    In the data you pass the dict in which to search. In args - keywords:
    data = {
        "first": {
            "second": "answer"
        }
    }
    you should pass:
    (data, "first", "second") - it will return "answer"
    (data, "first", "not_exist") - it will return None
    (data, "first", "second", "not_exist") - it will return None
    
    :param data: The dictionary to get the data from.
    :param args: keys.
    :param index: first args element.
    :return: The data from the dictionary.
    """
    if data:
        res = data.get(args[index])     # get data by key
        index = index + 1
    
        if index == len(args):          # if no keys - return result
            return res
        else:                           # if there are more keys
            if isinstance(res, dict):   # check its dict and go again
                return get_data_from_dicts(res, *args, index=index)
            else:
                return None             # if we have keys and in res not dict - not found
    else:
        return None


def update_coin(coin):
    try:
        __update_coin_data(coin)
    except ConnectionError:
        return f"{coin.symbol} wasn't updated. Try again later."
    
    score = __get_twitter_score(coin.twitter_id)
    
    __update_twitter_score(coin, score)
    
    coin.save()
    
    return f"{coin.symbol} was updated."


def __update_coin_data(coin):
    url = "https://api.coingecko.com/api/v3/coins/" + coin.coingecko_id + "?market_data=true" + \
          "&community_data=false&developer_data=false&sparkline=false&localization=false&tickers=false"
    content = requests.get(url)
    
    if content.status_code != 200:
        sleep(2)
        content = requests.get(url)
        if content.status_code != 200:
            raise ConnectionError(f"Error, code {content.status_code}")

    data = content.json()

    mc = get_data_from_dicts(data, "market_data", "market_cap", "usd")
    fdv = get_data_from_dicts(data, "market_data", "fully_diluted_valuation", "usd")
    volume = get_data_from_dicts(data, "market_data", "total_volume", "usd")
    price = get_data_from_dicts(data, "market_data", "current_price", "usd")

    coin.market_cap = mc if mc is not None else coin.market_cap
    coin.fdv = fdv if fdv is not None else coin.fdv
    coin.volume = volume if volume is not None else coin.volume
    coin.price = convert_price(price) if price is not None else coin.price


    twitter = get_data_from_dicts(data, "links", "twitter_screen_name")
    if twitter:
        if "?" in twitter:
            twitter = twitter.split("?")[0]
        
        # Aptos has wrong twitter on coingecko
        if len(twitter) < 16 and coin.symbol != "APT":
            coin.twitter_id = twitter

    site = get_data_from_dicts(data, "links", "homepage")
    if len(site) > 1:
        if isinstance(site, str) and len(site) < 200:
            coin.site = site
        elif isinstance(site, list) and len(site[0]) < 200:
            coin.site = site[0]


def __get_twitter_score(twitter):
    if not twitter:
        return None
    
    page = requests.get("https://twitterscore.io/twitter/" + twitter)

    if page.status_code != 200:
        return None
    
    soup = BeautifulSoup(page.content, 'html.parser')
    tag = soup.find("div", {"class": "progress"})
    
    try:
        return int(tag.get('data-target'))
    except ValueError:
        return None


def __update_twitter_score(coin, score):
    if score is None:
        print(f"Got error when tried to parse score, twitter: {coin.twitter_id}, symbol: {coin.symbol}")
        if coin.twitter_score is None:
            coin.twitter_score = 0
    else:
        coin.twitter_score = score
    
    if coin.twitter_score < 1:
        coin.coefficient_mc = 0
        coin.coefficient_fdv = 0
    else:
        if coin.market_cap:
            coin.coefficient_mc = coin.twitter_score / (coin.market_cap / 1000000)
        
        if coin.fdv:
            coin.coefficient_fdv = coin.twitter_score / (coin.fdv / 1000000)
