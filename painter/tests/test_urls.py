from incuna_test_utils.testcases.urls import URLTestCase

from .. import views


class TestPainterURLs(URLTestCase):
    def test_card_display_reload(self):
        self.assert_url_matches_view(
            view=views.CardDisplayReload,
            expected_url='/',
            url_name='card_display_reload',
        )

    def test_card_display_noreload(self):
        self.assert_url_matches_view(
            view=views.CardDisplay,
            expected_url='/noreload',
            url_name='card_display_noreload',
        )
