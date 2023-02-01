from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse

from .daemons import start_update_coin_daemon
from .daemons import start_update_score_daemon
from .forms import FilterForm
from .forms import DaemonForm
from .models import CryptoModel
from .models import DaemonModel
from .utils import update_coin

DEFAULT_FILTERS = {"order_by": FilterForm.ORDER_CHOICES[0], "lines": 100}


def index_view(request):
    return render(request, "index.html")


def stat_view(request):
    if request.method != "GET" and request.method != "POST":
        message = f"Not valid Method. I accept only GET and POST, you gave {request.method}"
        return render(request, "webstat/stat.html", context={"message": message})
    
    crypto = CryptoModel.objects.all()
    
    if request.method == "GET":
        form = FilterForm(initial=DEFAULT_FILTERS)
        
        crypto = crypto.order_by(FilterForm.ORDER_CHOICES[0][0])
        
        lines = DEFAULT_FILTERS.get("lines") if DEFAULT_FILTERS.get("lines") <= len(crypto) else len(crypto)
        crypto = crypto[:lines]
        
    if request.method == "POST":
        form = FilterForm(request.POST)
        
        if not form.is_valid():
            return render(request, "webstat/stat.html", context={"form": form})
        
        # Filters
        min_mc = form.cleaned_data.get("min_market_cap")
        if min_mc:
            crypto = crypto.filter(market_cap__gte=min_mc)
        max_mc = form.cleaned_data.get("max_market_cap")
        if max_mc:
            crypto = crypto.filter(market_cap__lte=max_mc)
            
        min_fdv = form.cleaned_data.get("min_fdv")
        if min_fdv:
            crypto = crypto.filter(fdv__gte=min_fdv)
        max_fdc = form.cleaned_data.get("max_fdv")
        if max_fdc:
            crypto = crypto.filter(fdv__lte=max_fdc)
        
        min_volume = form.cleaned_data.get("min_volume")
        if min_volume:
            crypto = crypto.filter(volume__gte=min_volume)
        max_volume = form.cleaned_data.get("max_volume")
        if max_volume:
            crypto = crypto.filter(volume__lte=max_volume)
            
        min_coeff_mc = form.cleaned_data.get("min_coeff_mc")
        if min_coeff_mc:
            crypto = crypto.filter(coefficient_mc__gte=min_coeff_mc)
        max_coeff_mc = form.cleaned_data.get("max_coeff_mc")
        if max_coeff_mc:
            crypto = crypto.filter(coefficient_mc__lte=max_coeff_mc)

        min_coeff_fdv = form.cleaned_data.get("min_coeff_fdv")
        if min_coeff_fdv:
            crypto = crypto.filter(coefficient_fdv__gte=min_coeff_fdv)
        max_coeff_fdv = form.cleaned_data.get("max_coeff_fdv")
        if max_coeff_fdv:
            crypto = crypto.filter(coefficient_fdv__lte=max_coeff_fdv)
            
        min_score = form.cleaned_data.get("min_score")
        if min_score:
            crypto = crypto.filter(twitter_score__gte=min_score)
        max_score = form.cleaned_data.get("max_score")
        if max_score:
            crypto = crypto.filter(twitter_score__lte=max_score)
            
        contains = form.cleaned_data.get("contains")
        if contains:
            crypto = crypto.filter(name__contains=contains)
        
        # Order by
        crypto = crypto.order_by(form.cleaned_data.get("order_by"))

        lines = form.cleaned_data.get("lines")
        if lines:
            lines = lines if lines <= len(crypto) else len(crypto)
            crypto = crypto[:lines]
        
        
    
    context = {"crypto": crypto, "form": form}
    return render(request, "webstat/stat.html", context=context)


def coin_view(request, pk):
    coin = get_object_or_404(CryptoModel, pk=pk)
    context = {"coin": coin}
    
    if request.method == "POST":
        message = update_coin(coin)
        context["message"] = message
    
    return render(request, "webstat/coin.html", context=context)


@staff_member_required
def update_view(request, pk):
    coin = CryptoModel.objects.get(pk=pk)
    message = update_coin(coin)
    
    return render(request, "webstat/coin.html", context={"coin": coin, "message": message})


@staff_member_required
def delete_view(request, pk):
    coin = get_object_or_404(CryptoModel, pk=pk)
    
    if request.method == "POST":
        close = "window.close();"
        coin.delete()
        return render(request, "webstat/delete.html", context={"close": close})
        
    
    return render(request, "webstat/delete.html", context={"coin": coin})


@staff_member_required
def control_view(request):
    daemon = DaemonModel.objects.get(pk=1)
    initial = {"coins_update_status": daemon.coins_update_status, "score_update_status": daemon.score_update_status}
    
    if request.method == "POST":
        form = DaemonForm(data=request.POST)
        if form.is_valid():
            coins_status = form.cleaned_data.get("coins_update_status")
            if coins_status != daemon.coins_update_status:
                daemon.coins_update_status = coins_status
                daemon.save()
                if coins_status:
                    start_update_coin_daemon()

            score_status = form.cleaned_data.get("score_update_status")
            if score_status != daemon.score_update_status:
                daemon.score_update_status = score_status
                daemon.save()
                if score_status:
                    start_update_score_daemon()
            
            return HttpResponseRedirect(reverse("control"))

    form = DaemonForm(initial=initial)
    info = {
        "coins_total_updated": daemon.coins_total_updated,
        "coins_current_update": daemon.coins_current_update,
        "coins_message": daemon.coins_message,
        "score_total_updated": daemon.score_total_updated,
        "score_current_update": daemon.score_current_update,
        "score_message": daemon.score_message,
    }
        
    context = {"form": form, "info": info}
    return render(request, "webstat/control.html", context=context)
