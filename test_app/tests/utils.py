from incuna_test_utils.testcases.request import BaseRequestTestCase

from . import factories


class RequestTestCase(BaseRequestTestCase):
    user_factory = factories.UserFactory
