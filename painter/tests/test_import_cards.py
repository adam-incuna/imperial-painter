from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from painter.management.commands.import_cards import Command
from painter.models import Card


class TestImportCards(TestCase):
    def __init__(self, *args, **kwargs):
        """
        Generate a mock CSV file, call the command to load it, and cache the resulting
        data locally rather than hitting the database every time we need it.

        The contents of the CSV file are drawn from self.input_data.  This data is built
        across several statements, each of which adds a line to it.  This is done so that
        each test method can be listed underneath the data it relies on.
        """
        csv_file = str(self.input_data)

        with mock.patch.object(Command, 'open_csv_file', return_value=csv_file):
            # We have to supply a file, but it will be ignored since we're mocking out
            # the open_csv_file method.
            call_command('import_cards', 'nonexistent_file.csv')

        self.output = {card.name: card for card in Card.objects.all()}
        return super().__init__(*args, **kwargs)

    input_data = 'name,template,Card Rules\n'
    input_data += 'a_card,a_template.html,some_data\n'
    def test_csv_columns(self):
        a_card = self.output['a_card']
        self.assertEqual(a_card.template_name, 'a_template.html')

        # The safe_headers method turns 'Card Rules' into 'card_rules'
        self.assertEqual(list(a_card.data.keys()), ['card_rules'])

    input_data += 'no_html_extension,test,\n'
    def test_template_name_fixing(self):
        self.assertEqual(self.output['no_html_extension'].template_name, 'test.html')

    input_data += 'non_newlined_rules,test,one_line\n'
    input_data += 'newlined_rules,test,"new\nline"\n'
    input_data += 'empty_rules,test,\n'
    def test_newline_forms_lists_everywhere(self):
        self.assertEqual(
            self.output['non_newlined_rules'].data,
            {'card_rules': ['one_line']}
        )
        self.assertEqual(
            self.output['newlined_rules'].data,
            {'card_rules': ['new', 'line']}
        )
        self.assertEqual(
            self.output['empty_rules'].data,
            {'card_rules': []}
        )
