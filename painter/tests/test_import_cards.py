from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from painter.management.commands.import_cards import Command
from painter.models import Card


class TestImportCards(TestCase):
    input_data = 'name,template,rules\n'
    input_data += 'card1,test,hello\n'
    input_data += 'card2,test,"new\nline"\n'

    def __init__(self, *args, **kwargs):
        csv_file = str(self.input_data)

        with mock.patch.object(Command, 'open_csv_file', return_value=csv_file):
            call_command('import_cards', 'nonexistent_file.csv')

        self.output = {card.name: card for card in Card.objects.all()}
        return super().__init__(*args, **kwargs)

    def test_object_creation(self):
        self.assertEqual(len(self.output), 2)

    def test_template_name(self):
        self.assertEqual(self.output['card1'].template_name, 'test.html')

    def test_newline_forms_lists(self):
        self.assertEqual(self.output['card1'].data, {'rules': ['hello']})
        self.assertEqual(self.output['card2'].data, {'rules': ['new', 'line']})
