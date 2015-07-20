from django.test import TestCase

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
