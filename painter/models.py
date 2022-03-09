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
        """
        Translate the stored template_name into a path to a template in the custom/ directory.
        """
        template = self.template_name

        if not template.endswith(".html"):
            template += ".html"

        if not template.startswith("custom/"):
            template = "custom/" + template

        return template

    class Meta:
        ordering = ['pk']
