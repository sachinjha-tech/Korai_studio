import pytest
from pages.home_page import HomePage


@pytest.fixture
def home_page(page):
    home = HomePage(page)
    home.goto()
    return home
