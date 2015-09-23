from incuna_test_utils.testcases.urls import URLTestCase

from .. import views


class TestPainterURLs(URLTestCase):
    def test_card_display(self):
        self.assert_url_matches_view(
            view=views.CardDisplay,
            expected_url='/',
            url_name='card_display',
        )

    def test_card_display_noreload(self):
        self.assert_url_matches_view(
            view=views.CardDisplay,
            expected_url='/noreload',
            url_name='card_display_noreload',
        )
