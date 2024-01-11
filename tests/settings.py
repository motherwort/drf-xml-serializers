import pytest
from django.conf import settings


@pytest.fixture
def pytest_configure():
    try:
        settings.configure(USE_I18N=False)
    except RuntimeError:
        pass
