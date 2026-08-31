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


def _case_info(item):
    """Return (kind, title, detail) that describe a test's scenario.

    `kind` comes from the optional `case` marker (POSITIVE / NEGATIVE / EDGE)
    and defaults to POSITIVE. `title`/`detail` fall back to the docstring.
    """
    doc = (item.function.__doc__ or "").strip()
    doc_lines = [ln.strip() for ln in doc.splitlines() if ln.strip()]
    title = doc_lines[0].rstrip(".") if doc_lines else item.name.replace("_", " ")
    detail = " ".join(doc_lines[1:]).strip() if len(doc_lines) > 1 else ""

    kind = "POSITIVE"
    marker = item.get_closest_marker("case")
    if marker is not None:
        if marker.args:
            kind = str(marker.args[0]).upper()
            if len(marker.args) > 1:
                title = str(marker.args[1])
        elif marker.kwargs.get("kind"):
            kind = str(marker.kwargs["kind"]).upper()
            if marker.kwargs.get("title"):
                title = str(marker.kwargs["title"])
    return kind, title, detail


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture a screenshot on failure and record each test's result/scenario."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if item.nodeid not in _results:
            kind, title, detail = _case_info(item)
            _results[item.nodeid] = {
                "kind": kind,
                "title": title,
                "detail": detail,
                "outcome": report.outcome,
            }
        else:
            _results[item.nodeid]["outcome"] = report.outcome

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
    """Write a scenario-aware test report into the screenshots folder."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SHOT_DIR / "final_results.txt"

    lines = [
        "=" * 70,
        " Korai Studio — UI Test Run Summary",
        f" Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f" Exit status: {exitstatus}",
        "=" * 70,
        "",
        f"{'#':<4} {'Scenario':<9} {'Result':<8} Test",
        "-" * 70,
    ]

    counts = {}
    for i, (nodeid, info) in enumerate(_results.items(), start=1):
        kind = info["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        outcome = info["outcome"].upper()
        lines.append(f"{i:<4} {kind:<9} {outcome:<8} {info['title']}")
        lines.append(f"          test    : {nodeid}")
        if info["detail"]:
            lines.append(f"          details : {info['detail']}")
        lines.append("")

    passed = sum(1 for r in _results.values() if r["outcome"] == "passed")
    failed = sum(1 for r in _results.values() if r["outcome"] == "failed")
    skipped = sum(1 for r in _results.values() if r["outcome"] == "skipped")

    scenario = "   ".join(f"{k}: {counts.get(k, 0)}" for k in ("POSITIVE", "NEGATIVE", "EDGE"))

    lines += [
        "=" * 70,
        f" TOTAL: {len(_results)}   PASSED: {passed}   FAILED: {failed}   "
        f"SKIPPED: {skipped}",
        f" SCENARIOS: {scenario}",
        "=" * 70,
    ]

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[conftest] Report written to {summary_path}")
