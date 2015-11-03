from django.core.management import call_command
from django.views.generic import ListView

from . import models


class CardDisplay(ListView):
    model = models.Card
    template_name = 'painter/card_display.html'


class CardDisplayReload(CardDisplay):
    def get(self, request, *args, **kwargs):
        call_command('import_cards', filenames=[])
        return super().get(request, *args, **kwargs)
