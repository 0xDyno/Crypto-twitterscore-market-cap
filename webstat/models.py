from django.db import models


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
    twitter_score_changes = models.CharField(max_length=5, blank=True)
    
    site = models.CharField(max_length=200, null=True)
    
    updated = models.DateTimeField(auto_now=True)
    create = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'all_crypto'
    
    def __str__(self):
        return "ID: {}, Symbol: {}".format(self.id, self.symbol)
    
    def get_coeff_mc(self):
        if self.twitter_score is not None and self.market_cap is not None:
            if self.twitter_score < 1:
                return None
            return self.twitter_score / self.market_cap * 1000000
        else:
            return None

    def get_coeff_fdv(self):
        if self.twitter_score is not None and self.fdv is not None:
            if self.twitter_score < 1:
                return None
            return self.twitter_score / self.fdv * 1000000
        else:
            return None
        
    # @classmethod
    # def one_time(cls):
    #     all = cls.objects.all()
    #     for c in all:
    #         pass
