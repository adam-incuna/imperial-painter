from unittest import mock

from . import factories
from .utils import RequestTestCase
from .. import views
from ..management.commands.import_cards import Command


class TestCardDisplay(RequestTestCase):
    view = views.CardDisplay

    def setUp(self):
        factories.CardFactory.create()
        self.request = self.create_request()
        self.view = self.get_view()

    def test_get(self):
        response = self.view(self.request)
        self.assertEqual(response.status_code, 200)


class TestCardDisplayReload(RequestTestCase):
    view = views.CardDisplayReload

    def setUp(self):
        self.request = self.create_request()
        self.view = self.get_view()

    def test_get(self):
        with mock.patch.object(Command, 'handle') as call_command:
            response = self.view(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(call_command.call_count, 1)
