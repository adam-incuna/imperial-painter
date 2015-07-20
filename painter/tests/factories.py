import factory

from django.contrib.auth.models import User
from incuna_test_utils.factories.user import BaseUserFactory

from .. import models


class CardFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Card {}'.format)
    template_name = 'template.html'
    data = {'item': 42}

    class Meta:
        model = models.Card


class UserFactory(BaseUserFactory):
    """Used for creating requests in view tests."""
    class Meta:
        model = User
