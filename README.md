# Korai Studio — UI Automation (pytest + Playwright + Page Object Model)

Automated UI tests for the live storefront **https://www.thekoraistudio.com/**,
built with **pytest-playwright** and the **Page Object Model (POM)**.

## Project structure

```
Korai_studio/
├── conftest.py              # Session-scoped browser/page + screenshot-on-failure hook
├── pytest.ini               # Pytest config: base_url, headed mode, HTML report
├── requirements.txt         # Python dependencies
├── .gitignore
├── screenshots/             # Failure screenshots (auto-generated)
├── reports/                 # HTML test reports (auto-generated)
├── pages/                   # Page Object Models
│   ├── __init__.py
│   ├── home_page.py         # HomePage — homepage + navigation + scroll/links
│   ├── login_page.py        # LoginPage — sign-in form
│   ├── register_page.py     # RegisterPage — create-account form
│   └── shop_page.py         # ShopPage — product grid + filter & sort panel
└── tests/                   # Test suites
    ├── __init__.py
    ├── test_registration.py # Registration flow (step 1)
    ├── test_login.py        # Login as sachin (step 2)
    ├── test_homepage.py     # Homepage scroll + link validation (step 3)
    ├── test_shop.py         # Shop filter & sort checks (step 4)
    └── test_navigation.py   # Main navigation + dropdown behaviour
```

## Prerequisites

- Python 3.9+ (tested on 3.14)
- Git (optional)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the Playwright browser (Chromium)
python -m playwright install chromium
```

## Running the tests

```bash
# Run the whole suite
pytest

# Run a single test file
pytest tests/test_registration.py

# Run a single test
pytest tests/test_navigation.py::test_cart_link_goes_to_bag_not_checkout

# Run headless (override the default headed mode)
pytest --headed=False
```

### Behaviour by default

- **Headed mode** — a visible browser window opens so you can watch the run.
- **HTML report** — generated automatically at `reports/report.html`
  (self-contained, open it in any browser).
- **Single session** — one browser window is opened and reused for the whole
  run via the session-scoped `context`/`page` fixtures.
- **Failure screenshots** — captured automatically on test failure and saved
  to `screenshots/`, then embedded into the HTML report.
- **Final results summary** — a per-test result recap is written to
  `screenshots/final_results.txt` after every run.
- **Deterministic execution order** — suites run in a fixed sequence
  (`registration → login → homepage → shop → navigation`) via `pytest-order`
  markers.

All of the above are configured in `pytest.ini` and `conftest.py`:

```ini
[pytest]
base_url = https://www.thekoraistudio.com
addopts = --headed --html=reports/report.html --self-contained-html
```

## Page Object Model

Each page is encapsulated in a class under `pages/` so tests interact with
meaningful methods instead of raw CSS/text selectors:

- `pages/home_page.py` — `HomePage`
- `pages/login_page.py` — `LoginPage`
- `pages/register_page.py` — `RegisterPage`

Page objects expose locators and actions (e.g. `goto()`, `click_nav()`,
`fill_form()`, `submit()`). Tests request a ready page object via fixtures
defined in `conftest.py` (`home_page`, `login_page`, `register_page`).

## Test flow

The suite runs as a single end-to-end journey (one browser session):

1. **Register** — the registration page is validated once (fields,
   constraints, cross-links); no real account is created.
2. **Login as sachin** — the sign-in form is validated, then sachin's
   credentials log the session in. The session stays signed in for the rest.
3. **Homepage** — while signed in, the page is scrolled top-to-bottom and
   back, and every link on the homepage is validated (well-formed hrefs and
   internal links resolving to a live page).
4. **Shop filters** — the shop filter & sort panel is exercised (sort by
   price, colour, design, price range) and the grid / querystring are verified.

## Test coverage

- **Homepage** — page loads, logo/title visible, announcement bar, hero
  carousel, featured products, signed-in header, full-page scroll, all-links
  validation.
- **Shop** — page loads signed in, filter panel widgets, sort by price
  (low/high), colour and design filters, price-range filter, reset to default.
- **Navigation** — primary nav links navigate to the correct pages, Collections
  dropdown (and its sub-group) reveal links, cart link goes to the bag — never
  into checkout/payment flows.
- **Registration** — page loads, field configuration, reachable from sign-in,
  mismatched passwords rejected; plus positive/negative/edge/boundary cases
  (valid form accepted, empty/invalid-email blocked, password min=8 boundary,
  field max-length clamping, email variants).
- **Login** — page loads, field configuration, sign-in button, forgot-password
  and create-account links, reachable from header/register, invalid credentials
  rejected, empty/malformed-email blocked, valid credential login (sachin).

## Reports & screenshots

After a run:

- `reports/report.html` — full HTML test report.
- `screenshots/*.png` — screenshot of the page at the moment of any failure.
- `screenshots/final_results.txt` — a scenario-aware report: each test listed
  as `# scenario result title` with test id + details, plus totals and a
  POSITIVE / NEGATIVE / EDGE scenario breakdown. Use the `@pytest.mark.case`
  marker to tag a test (e.g. `@pytest.mark.case("negative", "optional title")`);
  unmarked tests default to POSITIVE with their docstring as the title.

Both are git-ignored (`reports/`) or git-tracked via `.gitkeep` (`screenshots/`)
as appropriate.
