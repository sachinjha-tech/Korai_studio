import re
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage

SHOT_DIR = Path(__file__).parent / "screenshots"
_results = OrderedDict()


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
    """Capture a screenshot on failure and record the result of each test."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        _results[item.nodeid] = report.outcome

        if report.failed:
            page = item.funcargs.get("page")
            if page is not None and not page.is_closed():
                SHOT_DIR.mkdir(parents=True, exist_ok=True)
                nodeid = re.sub(r"[^A-Za-z0-9_.-]", "_", item.nodeid)
                shot_path = SHOT_DIR / f"{nodeid}.png"
                try:
                    # A short timeout keeps a hung page from masking the real
                    # failure with an INTERNALERROR.
                    page.screenshot(
                        path=str(shot_path), type="png", timeout=5000
                    )
                except Exception as exc:  # pragma: no cover - best effort only
                    print(f"[conftest] Screenshot failed for {nodeid}: {exc}")
                else:
                    try:
                        from pytest_html import extras
                        extra = extras.image(str(shot_path))
                        report.extras = getattr(report, "extras", []) + [extra]
                    except ImportError:
                        pass


def pytest_sessionfinish(session, exitstatus):
    """Write a final results summary into the screenshots folder."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SHOT_DIR / "final_results.txt"

    lines = [
        "=" * 62,
        " Korai Studio — UI Test Run Summary",
        f" Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f" Exit status: {exitstatus}",
        "=" * 62,
        "",
        f"{'#':<4} {'Test':<62} Result",
        "-" * 78,
    ]

    passed = sum(1 for r in _results.values() if r == "passed")
    failed = sum(1 for r in _results.values() if r == "failed")
    skipped = sum(1 for r in _results.values() if r == "skipped")

    for i, (nodeid, result) in enumerate(_results.items(), start=1):
        lines.append(f"{i:<4} {nodeid:<62} {result.upper()}")

    lines += [
        "",
        "=" * 62,
        f" TOTAL: {len(_results)}   PASSED: {passed}   FAILED: {failed}   "
        f"SKIPPED: {skipped}",
        "=" * 62,
    ]

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[conftest] Final results written to {summary_path}")
