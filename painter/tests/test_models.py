from django.test import TestCase

from . import factories
from .. import models


class TestCard(TestCase):
    model = models.Card

    def test_str(self):
        """A card's str representation is its name."""
        name = 'Leeroy Jenkins'
        card = factories.CardFactory.create(name=name)
        self.assertEqual(str(card), name)

    def test_get_template(self):
        """The method returns the template name if it has "custom/" already."""
        template_name = 'custom/leeroy.html'
        card = factories.CardFactory.create(template_name=template_name)
        self.assertEqual(card.get_template(), template_name)

    def test_get_template_adjustment(self):
        """The method returns the template name with "custom/" added if necessary."""
        template_name = 'leeroy.html'
        card = factories.CardFactory.create(template_name=template_name)
        self.assertEqual(card.get_template(), 'custom/' + template_name)
