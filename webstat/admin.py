from django.contrib import admin

from .models import CryptoModel
from .models import DaemonModel

admin.site.register(CryptoModel)
admin.site.register(DaemonModel)
