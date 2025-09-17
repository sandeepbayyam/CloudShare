from .models import Destination
from django.contrib import admin
from .models import Source, Destination

# Register your models here.
admin.site.register(Source)
admin.site.register(Destination)
