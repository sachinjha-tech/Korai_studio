import re
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage


# Share a single browser context and page for the entire run so every test
# executes in one session (one browser window) instead of a fresh one per test.
@pytest.fixture(scope="session")
def context(browser: Browser, browser_context_args: dict) -> BrowserContext:
    return browser.new_context(**browser_context_args)


@pytest.fixture(scope="session")
def page(context: BrowserContext) -> Page:
    return context.new_page()


@pytest.fixture
def home_page(page):
    home = HomePage(page)
    home.goto()
    return home


@pytest.fixture
def register_page(page):
    register = RegisterPage(page)
    register.goto()
    return register


@pytest.fixture
def login_page(page):
    login = LoginPage(page)
    login.goto()
    return login


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture a screenshot on failure and save it alongside the HTML report."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page is not None and not page.is_closed():
            project_root = Path(__file__).parent
            shot_dir = project_root / "screenshots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            nodeid = re.sub(r"[^A-Za-z0-9_.-]", "_", item.nodeid)
            shot_path = shot_dir / f"{nodeid}.png"
            page.screenshot(path=str(shot_path), type="png")
            try:
                from pytest_html import extras
                extra = extras.image(str(shot_path))
                report.extras = getattr(report, "extras", []) + [extra]
            except ImportError:
                pass
