from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Evento)
admin.site.register(Prenotazione)
admin.site.register(Recensione)
admin.site.register(Tag)