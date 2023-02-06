import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .daemons import start_update_coin_daemon
from .daemons import start_update_score_daemon
from .forms import CoinForm
from .forms import ControlForm
from .forms import FilterForm
from .models import CryptoModel
from .models import DaemonModel
from .utils import add_new_coin
from .utils import update_coin
from .utils import custom_sort

DEFAULT_FILTERS = {"order_by": FilterForm.ORDER_CHOICES[0], "lines": 100}
DEFAULT_ORDER_BY = [
    "-market_cap", "market_cap",
    "-fdv", "fdv",
]


def index_view(request):
    return render(request, "index.html")


def stat_view(request):
    if request.method != "GET" and request.method != "POST":
        messages.error(request, f"Not valid Method. I accept only GET and POST, you gave {request.method}")
        return render(request, "webstat/stat.html")
    
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
        if min_mc is not None:
            crypto = crypto.filter(market_cap__gte=min_mc)
        max_mc = form.cleaned_data.get("max_market_cap")
        if max_mc is not None:
            crypto = crypto.filter(market_cap__lte=max_mc)
            
        min_fdv = form.cleaned_data.get("min_fdv")
        if min_fdv is not None:
            crypto = crypto.filter(fdv__gte=min_fdv)
        max_fdc = form.cleaned_data.get("max_fdv")
        if max_fdc is not None:
            crypto = crypto.filter(fdv__lte=max_fdc)
        
        min_volume = form.cleaned_data.get("min_volume")
        if min_volume is not None:
            crypto = crypto.filter(volume__gte=min_volume)
        max_volume = form.cleaned_data.get("max_volume")
        if max_volume is not None:
            crypto = crypto.filter(volume__lte=max_volume)
            
        min_coeff_mc = form.cleaned_data.get("min_coeff_mc")
        if min_coeff_mc is not None:
            crypto = crypto.filter(coefficient_mc__gte=min_coeff_mc)
        max_coeff_mc = form.cleaned_data.get("max_coeff_mc")
        if max_coeff_mc is not None:
            crypto = crypto.filter(coefficient_mc__lte=max_coeff_mc)

        min_coeff_fdv = form.cleaned_data.get("min_coeff_fdv")
        if min_coeff_fdv is not None:
            crypto = crypto.filter(coefficient_fdv__gte=min_coeff_fdv)
        max_coeff_fdv = form.cleaned_data.get("max_coeff_fdv")
        if max_coeff_fdv is not None:
            crypto = crypto.filter(coefficient_fdv__lte=max_coeff_fdv)
            
        min_score = form.cleaned_data.get("min_score")
        if min_score is not None:
            crypto = crypto.filter(twitter_score__gte=min_score)
        max_score = form.cleaned_data.get("max_score")
        if max_score is not None:
            crypto = crypto.filter(twitter_score__lte=max_score)
            
        contains = form.cleaned_data.get("contains")
        if contains is not None:
            crypto = crypto.filter(Q(name__icontains=contains) | Q(symbol__icontains=contains))
        
        # Order by
        order_by = form.cleaned_data.get("order_by")
        if order_by in DEFAULT_ORDER_BY:
            crypto = crypto.order_by(order_by)
        else:
            crypto = custom_sort(order_by, crypto)
            
        lines = form.cleaned_data.get("lines")
        if lines:
            lines = lines if lines <= len(crypto) else len(crypto)
            crypto = crypto[:lines]
            
    
    context = {"crypto": crypto, "form": form}
    return render(request, "webstat/stat.html", context=context)


@staff_member_required
def coin_view(request, pk):
    coin = get_object_or_404(CryptoModel, pk=pk)
    
    initial = {
        "twitter": coin.twitter_id if coin.twitter_id is not None else "",
        "twitter_score": coin.twitter_score if coin.twitter_score is not None else 0,
    }
    if request.method == "GET":
        form = CoinForm(initial=initial)
    
    if request.method == "POST":
        form = CoinForm(request.POST)
        if form.is_valid():
            twitter = form.cleaned_data.get("twitter")
            if len(twitter) < 16:
                coin.twitter_id = twitter
            else:
                messages.error(request, message="Twitter is too long")
            
            coin.twitter_score = form.cleaned_data.get("twitter_score")
            coin.save()
        else:
            messages.error(request, "Not valid")

    context = {"coin": coin, "form": form}
    return render(request, "webstat/coin.html", context=context)


@staff_member_required
def update_view(request, pk):
    coin = CryptoModel.objects.get(pk=pk)
    res = update_coin(coin)
    
    if res:
        messages.success(request, f"{coin.symbol} was updated.")
    else:
        messages.error(request, f"{coin.symbol} wasn't updated. Try again later.")
    
    return HttpResponseRedirect(reverse("coin", kwargs={"pk": pk}))


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
        form = ControlForm(data=request.POST)
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
                    
            new_coin = form.cleaned_data.get("new_coin")
            if new_coin:
                try:
                    result = add_new_coin(new_coin)
    
                    if result:
                        messages.success(request, message="New coin added.")
                        return HttpResponseRedirect(reverse("coin", kwargs={"pk": result.pk}))
                    else:
                        messages.error(request, message="Wasn't able to add coin")
                except Exception as e:
                    messages.error(request, message=f"Unknown error occurred: {str(e)}")
            
            return HttpResponseRedirect(reverse("control"))

    form = ControlForm(initial=initial)
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
