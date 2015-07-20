from django.test import TestCase

from . import factories
from .. import models


class TestCard(TestCase):
    model = models.Card

    def test_fields(self):
        """Boring model test."""
        expected_fields = {
            'id',
            'name',
            'template_name',
            'data',
        }

        fields = self.model._meta.get_all_field_names()
        self.assertCountEqual(fields, expected_fields)

    def test_str(self):
        """A card's str representation is its name."""
        name = 'Leeroy Jenkins'
        card = factories.CardFactory.create(name=name)
        self.assertEqual(str(card), name)
