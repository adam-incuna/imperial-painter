import datetime

from django.core.validators import MinValueValidator
from django.db import models
from jsonfield import JSONField


class Card(models.Model):
    """A single card entry."""
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    data = JSONField(default={})

    def __str__(self):
        return self.name

    def get_template(self):
        if self.template_name.startswith('custom/'):
            return self.template_name
        return 'custom/' + self.template_name

    class Meta:
        ordering = ['pk']


class DataFile(models.Model):
    """Stores the name of a CSV file that data was loaded from."""
    name = models.CharField(max_length=255)
    date_loaded = models.DateField(default=datetime.datetime.now)
