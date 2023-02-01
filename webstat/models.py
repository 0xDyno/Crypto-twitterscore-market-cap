from datetime import datetime
from time import sleep

import requests
from django.db import models

from .utils import convert_price
from .utils import get_data_from_dicts


class DaemonModel(models.Model):
    coins_update_status = models.BooleanField()
    coins_total_updated = models.IntegerField(default=0)
    coins_current_update = models.CharField(max_length=15, blank=True, default="")
    coins_message = models.CharField(max_length=300, blank=True, null=True, default="")
    
    score_update_status = models.BooleanField()
    score_total_updated = models.IntegerField(default=0)
    score_current_update = models.CharField(max_length=15, blank=True, default="")
    score_message = models.CharField(max_length=300, blank=True, null=True, default="")
    
    class Meta:
        db_table = "daemon_service"


class CryptoModel(models.Model):
    # longer than 5 - it wierd, loger than 10 - wrong
    symbol = models.CharField(max_length=10)
    
    # max 53 if symbol < 10
    name = models.CharField(max_length=100)
    
    # max 54 if symbol < 10
    coingecko_id = models.CharField(max_length=100, null=True)
    coinmarketcap_id = models.CharField(max_length=100, null=True)
    
    # I want to save price as text and format numbers into text before saving
    price = models.CharField(max_length=10, null=True)
    
    market_cap = models.IntegerField(null=True)
    fdv = models.IntegerField(null=True)
    
    volume = models.IntegerField(null=True)
    
    twitter_id = models.CharField(max_length=15, null=True)
    twitter_score = models.IntegerField(null=True)
    coefficient_mc = models.FloatField(null=True)
    coefficient_fdv = models.FloatField(null=True)
    
    site = models.CharField(max_length=200, null=True)
    
    updated = models.DateTimeField(auto_now=True)
    create = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'all_crypto'
    
    def __str__(self):
        return "ID: {}, Symbol: {}".format(self.id, self.symbol)
    
    @classmethod
    def parse_coins(cls):
        do_action = input("Are you sure to delete all data and continue? write \"delete\" for yes >> ")
        if not do_action == "delete":
            return
        
        url = "https://api.coingecko.com/api/v3/coins/list?include_platform=false"
        response = requests.get(url).json()
        
        all_data = cls.objects.all()
        for data in all_data:
            data.delete()
        
        for data in response:
            new_coin = cls()
            name = data.get("name")
            symbol = data.get("symbol")
            coingecko_id = data.get("id")
            
            if len(name) < 60 and len(symbol) < 7:
                new_coin.name = name
                new_coin.symbol = symbol.upper()
                new_coin.coingecko_id = coingecko_id if " " not in coingecko_id else coingecko_id.replace(" ", "-")
                new_coin.save()
    
    @classmethod
    def parse_coin_data(cls):
        all_coins = cls.objects.all()
        for coin in all_coins:
            if coin.price is not None:  # if we have the price - skip
                continue
            print(f"Start working with {coin.name} ({coin.symbol}), gecko id - {coin.coingecko_id}")
            
            data = cls.get_coin_data(coin)
            if data is None:
                continue
            
            mc = get_data_from_dicts(data, "market_data", "market_cap", "usd")
            market_cap = mc if mc is not None else 0
            
            fdv = get_data_from_dicts(data, "market_data", "fully_diluted_valuation", "usd")
            fdv = fdv if fdv is not None else 0
            
            # if MarketCap and FDV is less, than 100000 - we can't work with such coin and we have to delete it.
            minc = 100000
            if market_cap < minc and fdv < minc:
                print(f"{coin.name} ({coin.symbol}), gecko id - {coin.coingecko_id}\n"
                      f"market cap = {market_cap}, fdv = {fdv}. To delete.")
                coin.delete()
                sleep(4)
                continue
            else:
                coin.market_cap = market_cap if market_cap > minc else None
                coin.fdv = fdv if fdv > minc else None
            
            coin.volume = get_data_from_dicts(data, "market_data", "total_volume", "usd")
            
            price = get_data_from_dicts(data, "market_data", "current_price", "usd")
            if price:
                coin.price = convert_price(price)
            
            twitter = get_data_from_dicts(data, "links", "twitter_screen_name")
            if twitter:
                if "?" in twitter:
                    twitter = twitter.split("?")[0]
                
                if len(twitter) < 16:
                    coin.twitter_id = twitter
            
            site = get_data_from_dicts(data, "links", "homepage")
            if len(site) > 1:
                if isinstance(site, str) and len(site) < 200:
                    coin.site = site
                elif isinstance(site, list) and len(site[0]) < 200:
                    coin.site = site[0]
            
            coin.save()
            
            sleep(4)
            
            
    @staticmethod
    def get_coin_data(coin):
        url = "https://api.coingecko.com/api/v3/coins/" + coin.coingecko_id
        url += "?localization=false" \
               "&tickers=false" \
               "&market_data=true" \
               "&community_data=false" \
               "&developer_data=false" \
               "&sparkline=false"
    
        content = requests.get(url)
    
        if content.status_code == 404:
            print(f"Error 404. Deleted. ID {coin.coingecko_id}")
            coin.delete()
            return None
    
        while content.status_code != 200:
            print(f"Code: {content.status_code}. ID: {coin.coingecko_id}. Sleeping...")
            sleep(10)
            content = requests.get(url)
        
        return content.json()
    
    
    @classmethod
    def parse_twitter_score(cls):
        from bs4 import BeautifulSoup
        
        try:
            while True:
                all_coins = cls.objects.all()
                for coin in all_coins:
                    if coin.twitter_score is not None or coin.twitter_id is None:
                        continue
            
                    url = "https://twitterscore.io/twitter/" + coin.twitter_id
            
                    page = requests.get(url)
            
                    if page.status_code != 200:
                        if page.status_code == 404:
                            coin.twitter_id = None
                            coin.save()
                        print(f"Got error, code: {page.status_code}, page: {coin.twitter_id}, symbol: {coin.symbol}")
                        continue
            
                    # Use BeautifulSoup to parse the HTML content of the page
                    soup = BeautifulSoup(page.content, 'html.parser')
            
                    # Find the tag with the class "progress"
                    score_text = soup.find('div', {'class': 'progress'}).get("target")
            
                    # Convert the extracted string to an integer
                    score = int(score_text)
            
                    coin.twitter_score = score
            
                    if score == 0:
                        coin.coefficient_mc = 0
                        coin.coefficient_fdv = 0
                    else:
                        if coin.market_cap:
                            coin.coefficient_mc = score / (coin.market_cap / 1000000)
                
                        if coin.fdv:
                            coin.coefficient_fdv = score / (coin.fdv / 1000000)
            
                    coin.save()
                print("Finished, sleeping...")
                sleep(600)
        except InterruptedError:
            print("Finished")
    
    @classmethod
    def one_time(cls):
        all_coins = cls.objects.filter(name__contains="[OLD]")
        for coin in all_coins:
            coin.delete()
