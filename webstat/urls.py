from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path("stat/", views.stat_view, name="stat"),
    path("control/", views.control_view, name="control"),
    path("stat/coin/<int:pk>/", views.coin_view, name="coin"),
    path("stat/coin/update/<int:pk>/", views.update_view, name="update"),
    path("stat/coin/delete/<int:pk>/", views.delete_view, name="delete"),
]