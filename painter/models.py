from django.db import models
from jsonfield import JSONField


class Card(models.Model):
    """A single card entry."""
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    data = JSONField(default={})

    def __str__(self):
        return self.name
