import logging
import re
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

# Generous global default so slow storefront responses don't trip the suite.
expect.set_options(timeout=20_000)
from pages.api_client import KoraiAPI
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage

BASE_DIR = Path(__file__).parent
SHOT_DIR = BASE_DIR / "screenshots"
LOG_DIR = BASE_DIR / "reports" / "logs"
_results = OrderedDict()

# ---------------------------------------------------------------------------
# Logging — a timestamped file per run, ready to share with stakeholders.
# ---------------------------------------------------------------------------

LOGFILE_PATH = LOG_DIR / datetime.now().strftime("korai_run_%Y%m%d_%H%M%S.log")


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("korai.ui")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(str(LOGFILE_PATH), encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    return logger


LOGGER = _setup_logger()


def _wire_page_logging(page: Page) -> None:
    """Record browser console warnings/errors and failed HTTP responses."""
    def _console(msg):
        if msg.type in ("error", "warning"):
            text = msg.text.strip().replace("\n", " ")[:400]
            LOGGER.info("PAGE   console[%s]: %s", msg.type, text)

    def _response(resp):
        if resp.status >= 400:
            LOGGER.warning("PAGE   HTTP %s %s", resp.status, resp.url)

    page.on("console", _console)
    page.on("response", _response)


# ---------------------------------------------------------------------------
# Per-test browser isolation.
#
# Every test gets its own fresh, isolated browser context and page (function
# scoped). Authenticated tests load sachin's saved session (storage_state) so
# they start already signed in without sharing a live page; anonymous tests
# (login, registration, logout, anonymous API) use dedicated anonymous
# contexts. This makes the suite safe to run with `pytest -n auto`.
# ---------------------------------------------------------------------------


# Force every test that touches sachin's LIVE cart/wishlist/session onto a
# single worker (via `--dist=loadgroup`) so they never run concurrently
# against the same account state. Stateless tests stay ungrouped and
# parallelize across the remaining workers.
ACCOUNT_STATE_GROUP = "account-state"


# -- authenticated session cache (one real login per worker) ----------------

@pytest.fixture(scope="session")
def base_url(pytestconfig) -> str | None:
    """Resolve the target site, also inside xdist workers.

    pytest-base-url only copies the `base_url` ini value into
    `config.option.base_url` in the MAIN process (it skips worker nodes), so
    workers would otherwise lose it and relative URL navigations would fail
    with "Cannot navigate to invalid URL". This shadow fixture falls back to
    the ini value so every worker resolves the same base URL.
    """
    return pytestconfig.getoption("base_url") or pytestconfig.getini("base_url") or None


@pytest.fixture(scope="session")
def auth_state(browser: Browser, browser_context_args: dict) -> dict | None:
    """The authenticated storage_state (as sachin), or None.

    Session-scoped, so it runs exactly once per worker process: one real login
    per worker, reused as the starting storage_state for every authenticated
    test in that worker. The session is kept in memory only (no on-disk cache,
    which could otherwise let a stale/expired cookie leak between runs).
    """
    from utils import USER_EMAIL, USER_PASSWORD

    # Perform a real sign-in in a throwaway context to capture the session.
    ctx = browser.new_context(**browser_context_args)
    page = ctx.new_page()
    try:
        page.goto("/account/login", wait_until="networkidle")
        page.locator("#email").fill(USER_EMAIL)
        page.locator("#password").fill(USER_PASSWORD)
        with page.expect_navigation(wait_until="load", timeout=30000):
            page.locator('form[action="/account/login"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")
        # Confirm the session actually stuck before caching it.
        if not page.url.rstrip("/").endswith("/account"):
            raise RuntimeError(
                f"auth-state login did not reach /account (got {page.url}); "
                "check USER credentials in utils.py"
            )
        return ctx.storage_state()
    finally:
        ctx.close()


# -- authenticated fixtures (default) -----------------------------------------


@pytest.fixture(scope="function")
def context(browser: Browser, browser_context_args: dict,
            auth_state: dict | None) -> BrowserContext:
    """A fresh, isolated context; authenticated as sachin by default."""
    if auth_state is None:
        return browser.new_context(**browser_context_args)
    return browser.new_context(storage_state=auth_state, **browser_context_args)


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    _wire_page_logging(page)
    return page


# -- anonymous fixtures (logged-out) ------------------------------------------


@pytest.fixture(scope="function")
def anon_context(browser: Browser, browser_context_args: dict) -> BrowserContext:
    """A fresh, isolated, logged-out context (for login/register/logout/anon API)."""
    return browser.new_context(**browser_context_args)


@pytest.fixture(scope="function")
def anon_page(anon_context: BrowserContext) -> Page:
    page = anon_context.new_page()
    _wire_page_logging(page)
    return page


@pytest.fixture
def home_page(page):
    home = HomePage(page)
    home.goto()
    return home


@pytest.fixture
def register_page(anon_page):
    register = RegisterPage(anon_page)
    register.goto()
    return register


@pytest.fixture
def login_page(anon_page):
    login = LoginPage(anon_page)
    login.goto()
    return login


@pytest.fixture
def cart_page(page):
    cart = CartPage(page)
    cart.goto()
    return cart


@pytest.fixture
def checkout_page(page):
    checkout = CheckoutPage(page)
    checkout.goto()
    return checkout


@pytest.fixture
def api(playwright, base_url):
    """A fresh, session-aware HTTP client for the API test layer."""
    client = playwright.request.new_context(base_url=base_url)
    yield KoraiAPI(client, base_url)
    client.dispose()


# ---------------------------------------------------------------------------
# Scenario metadata for the report.
# ---------------------------------------------------------------------------


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


def _capture(page, nodeid) -> Path | None:
    """Best-effort screenshot for a test; never lets a failure escape."""
    if page is None or page.is_closed():
        return None
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", nodeid)
    path = SHOT_DIR / f"{name}.png"
    try:
        # A short timeout keeps a hung page from masking the real failure.
        page.screenshot(path=str(path), type="png", timeout=5000)
        return path
    except Exception as exc:  # pragma: no cover - best effort only
        LOGGER.warning("screenshot failed for %s: %s", nodeid, exc)
        return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Log every test and capture a screenshot (pass or fail)."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "setup":
        LOGGER.info("START  %s", item.nodeid)

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

        # The test may use an authenticated page or an anonymous page.
        page = item.funcargs.get("page") or item.funcargs.get("anon_page")
        url = getattr(page, "url", "") if page is not None else ""
        LOGGER.info(
            "END    %-100s scenario=%s result=%s duration=%.2fs url=%s",
            item.nodeid,
            _results[item.nodeid]["kind"],
            report.outcome,
            getattr(call, "duration", 0),
            url,
        )

        shot_path = _capture(page, item.nodeid)
        if shot_path is not None:
            try:
                from base64 import b64encode
                from pytest_html import extras
                payload = b64encode(shot_path.read_bytes()).decode("ascii")
                extra = extras.image(payload, mime_type="image/png")
                report.extras = getattr(report, "extras", []) + [extra]
            except ImportError:
                pass


def pytest_sessionstart(session):
    LOGGER.info("=" * 70)
    LOGGER.info("SESSION START  base_url=%s", session.config.getini("base_url"))
    LOGGER.info("log file: %s", LOGFILE_PATH)
    LOGGER.info("=" * 70)


def pytest_sessionfinish(session, exitstatus):
    """Write a scenario-aware test report into the screenshots folder."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = SHOT_DIR / "final_results.txt"

    lines = [
        "=" * 70,
        " Korai Studio — UI Test Run Summary",
        f" Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f" Exit status: {exitstatus}",
        f" Log file: {LOGFILE_PATH}",
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

    LOGGER.info("=" * 70)
    LOGGER.info(
        "SESSION END  total=%d passed=%d failed=%d skipped=%d  scenarios=%s",
        len(_results), passed, failed, skipped,
        scenario.replace(" ", ""),
    )
    LOGGER.info("report: %s", summary_path)
    LOGGER.info("=" * 70)

    print(f"\n[conftest] Report written to {summary_path}")
    print(f"[conftest] Log written to {LOGFILE_PATH}")