from unittest import mock

import pytest


@pytest.fixture(autouse=True, scope="package")
def mock_sleep():
    with mock.patch("asyncio.sleep"):
        yield
