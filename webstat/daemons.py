from random import randint
from threading import Thread
from time import sleep

from .models import CryptoModel
from .models import DaemonModel
from .utils import __get_twitter_score
from .utils import __update_twitter_score
from .utils import __update_coin_data

SCORE = "score"
COINS = "coins"


def start_update_coin_daemon():
    thread = Thread(target=update_coins)
    print("here1")
    thread.start()


def start_update_score_daemon():
    thread = Thread(target=update_score)
    thread.start()


def update_coins():
    try:
        while DaemonModel.objects.get(pk=1).coins_update_status:
            coins = CryptoModel.objects.all()
            for coin in coins:
                if not DaemonModel.objects.get(pk=1).coins_update_status:
                    break
                    
                settings = DaemonModel.objects.get(pk=1)
                settings.coins_current_update = coin.symbol
                settings.coins_total_updated += 1
                settings.save()
                
                try:
                    __update_coin_data(coin)
                except ConnectionError as error:
                    message = "last error: " + error.__str__()
                    settings = DaemonModel.objects.get(pk=1)
                    if len(message) > 300:
                        settings.message = message
                    else:
                        settings.message = message[:300]
                    settings.save()
                
                sleep(15)
    
    except Exception as error:
        save_error(error, COINS)
        

def update_score():
    try:
        while DaemonModel.objects.get(pk=1).score_update_status:
            coins = CryptoModel.objects.all()
            for coin in coins:
                if not DaemonModel.objects.get(pk=1).score_update_status:
                    break
                    
                if not coin.twitter_id:
                    continue
                
                settings = DaemonModel.objects.get(pk=1)
                settings.score_total_updated = settings.score_total_updated + 1
                settings.score_current_update = coin.symbol
                settings.save()

                score = __get_twitter_score(coin.twitter_id)
                
                __update_twitter_score(coin, score)
                
                coin.save()
                
                sleep(randint(50, 100))
    except Exception as error:
        save_error(error, SCORE)


def save_error(error, type_):
    settings = DaemonModel.objects.get(pk=1)
    
    if type_ == COINS:
        settings.coins_update_status = False
        settings.coins_message = error.__str__()
    if type_ == SCORE:
        settings.score_update_status = False
        settings.score_message = error.__str__()
    settings.save()