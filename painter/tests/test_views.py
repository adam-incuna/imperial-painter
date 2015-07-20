from . import factories
from .utils import RequestTestCase
from .. import views


class TestCardDisplay(RequestTestCase):
    view = views.CardDisplay

    def setUp(self):
        self.card = factories.CardFactory.create()
        self.request = self.create_request()
        self.view = self.get_view()

    def test_get(self):
        response = self.view(self.request)
        self.assertEqual(response.status_code, 200)
