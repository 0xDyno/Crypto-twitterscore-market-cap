from django import forms
from django.core.validators import ValidationError

from .models import DaemonModel


class DaemonForm(forms.Form):
    coins_update_status = forms.BooleanField(required=False)
    score_update_status = forms.BooleanField(required=False)


class FilterForm(forms.Form):
    ORDER_CHOICES = [
        ("-market_cap", "high to low - Market Cap "),
        ("-fdv", "high to low - FDV"),
        ("-coefficient_mc", "high to low - Coeff MC"),
        ("-coefficient_fdv", "high to low - Coeff FDV"),
        
        ("market_cap", "low to high - Market Cap"),
        ("fdv", "low to high - FDV"),
        ("coefficient_mc", "low to high - Coeff MC"),
        ("coefficient_fdv", "low to high - Coeff FDV"),
    ]

    min_market_cap = forms.IntegerField(min_value=100000, required=False)
    max_market_cap = forms.IntegerField(min_value=100000, required=False)
    min_fdv = forms.IntegerField(min_value=100000, required=False)
    max_fdv = forms.IntegerField(min_value=100000, required=False)
    
    min_volume = forms.IntegerField(min_value=100, required=False)
    max_volume = forms.IntegerField(min_value=100, required=False)
    
    min_score = forms.IntegerField(required=False)
    max_score = forms.IntegerField(required=False)
    
    min_coeff_mc = forms.FloatField(step_size=0.01, required=False)
    max_coeff_mc = forms.FloatField(step_size=0.01, required=False)
    
    min_coeff_fdv = forms.FloatField(step_size=0.01, required=False)
    max_coeff_fdv = forms.FloatField(step_size=0.01, required=False)
    
    contains = forms.CharField(max_length=100, required=False)
    lines = forms.IntegerField(min_value=1, required=False)
    order_by = forms.ChoiceField(choices=ORDER_CHOICES)
    
    
    def clean_max_market_cap(self):
        min_mc = self.cleaned_data.get("min_market_cap")
        max_mc = self.cleaned_data.get("max_market_cap")
        
        if min_mc is not None and max_mc is not None:
            if min_mc > max_mc:
                raise ValidationError(message="min Market Cap can't be smaller than max Market Cap")
        return max_mc
    
    def clean_max_fdv(self):
        min_fdv = self.cleaned_data.get("min_fdv")
        max_fdv = self.cleaned_data.get("max_fdv")
        
        if min_fdv is not None and max_fdv is not None:
            if min_fdv > max_fdv:
                raise ValidationError(message="min FDV can't be smaller than max FDV")
        return max_fdv
        
    def clean_max_volume(self):
        min_volume = self.cleaned_data.get("min_volume")
        max_volume = self.cleaned_data.get("max_volume")
        
        if min_volume is not None and max_volume is not None:
            if min_volume > max_volume:
                raise ValidationError(message="min Volume can't be smaller than max Volume")
        return max_volume
    
    def clean_max_score(self):
        min_score = self.cleaned_data.get("min_score")
        max_score = self.cleaned_data.get("max_score")

        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValidationError(message="min Score can't be smaller than max Score")
        return max_score
    
    def clean_max_coeff_mc(self):
        min_coeff_mc = self.cleaned_data.get("min_coeff_mc")
        max_coeff_mc = self.cleaned_data.get("max_coeff_mc")

        if min_coeff_mc is not None and max_coeff_mc is not None:
            if min_coeff_mc > max_coeff_mc:
                raise ValidationError(message="min Coeff MC can't be smaller than max Coeff MC")
        return max_coeff_mc
    
    def clean_max_coeff_fdv(self):
        min_coeff_fdv = self.cleaned_data.get("min_coeff_fdv")
        max_coeff_fdv = self.cleaned_data.get("max_coeff_fdv")

        if min_coeff_fdv is not None and max_coeff_fdv is not None:
            if min_coeff_fdv > max_coeff_fdv:
                raise ValidationError(message="min Coeff FDV can't be smaller than max Coeff FDV")
        return max_coeff_fdv

    def clean_contains(self):
        contains = self.cleaned_data.get("contains")
        if contains is not None:
            return contains.strip().lower()
        return contains
