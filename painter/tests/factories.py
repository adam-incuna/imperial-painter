import factory

from .. import models


class CardFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Card {}'.format)
    template_name = 'template.html'
    data = {'item': 42}

    class Meta:
        model = models.Card
