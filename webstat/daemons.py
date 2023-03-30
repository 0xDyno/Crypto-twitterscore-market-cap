import traceback
from random import randint
from threading import Thread
from time import sleep

from .models import CryptoModel
from .models import DaemonModel
from .utils import __get_twitter_score
from .utils import __get_twitter_score_changes
from .utils import __update_twitter_score
from .utils import __update_twitter_score_changes
from .utils import __update_coin_data

SCORE = "score"
COINS = "coins"


def start_update_coin_daemon():
    thread = Thread(target=update_coins)
    thread.start()


def start_update_score_daemon():
    thread = Thread(target=update_score)
    thread.start()


def update_coins():
    try:
        while DaemonModel.objects.get(pk=1).coins_update_status:
            last = DaemonModel.objects.get(pk=1).coins_current_update
            all_coins = CryptoModel.objects.all()
            coins = get_list_from_last_coin(last, all_coins)
            coins = coins if len(coins) > 1 else all_coins  # check we're not in the loop with only 1 last coin
                
            for coin in coins:
                if not DaemonModel.objects.get(pk=1).coins_update_status:
                    break
                    
                settings = DaemonModel.objects.get(pk=1)
                settings.coins_current_update = coin.symbol
                settings.coins_total_updated += 1
                settings.save()
                
                try:
                    __update_coin_data(coin)
                    print(f"Updated coin info for {coin.symbol}")
                    coin.save()
                except ConnectionError as error:
                    message = "last error: " + error.__str__()
                    settings = DaemonModel.objects.get(pk=1)
                    if len(message) > 300:
                        settings.message = message
                    else:
                        settings.message = message[:300]
                    settings.save()
                    
                sleep(15)
                
            settings = DaemonModel.objects.get(pk=1)
            settings.coins_current_update = ""
            settings.save()
    
    except Exception as error:
        traceback.print_exc()
        save_error(error, COINS)
        

def update_score():
    try:
        while DaemonModel.objects.get(pk=1).score_update_status:
            last = DaemonModel.objects.get(pk=1).score_current_update
            all_coins = CryptoModel.objects.all()
            coins = get_list_from_last_coin(last, all_coins)
            coins = coins if len(coins) > 1 else all_coins      # check we're not in the loop with only 1 last coin

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
                changes = __get_twitter_score_changes(coin.twitter_id)
                
                __update_twitter_score(coin, score)
                __update_twitter_score_changes(coin, changes)
                
                coin.save()
                
                sleep(randint(50, 100))
    except Exception as error:
        save_error(error, SCORE)
        
        
def get_list_from_last_coin(last_coin: str, all_coins):
    if last_coin:
        for i, coin in enumerate(all_coins):
            if coin.symbol == last_coin:
                return all_coins[i:]
    return all_coins


def save_error(error, type_):
    settings = DaemonModel.objects.get(pk=1)
    
    if type_ == COINS:
        settings.coins_update_status = False
        settings.coins_message = f"Critical Error: {error.__str__()}"
    if type_ == SCORE:
        settings.score_update_status = False
        settings.score_message = f"Critical Error: {error.__str__()}"
    settings.save()