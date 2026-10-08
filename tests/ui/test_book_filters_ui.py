import re
import pytest
from playwright.sync_api import Page, expect
from scripts.seed import build_books

FILTER_LABELS = ["Book Format", "Language", "Publication Date", "Customer Reviews"]
CATEGORY_NAMES = ["Fiction", "Non-Fiction"]
SEED_COLUMNS = ("title", "author", "category", "format", "language",
                "publication_date", "customer_rating", "price")

# Literal cutoffs for the frozen test date (2026-08-31), written out by hand so the UI
# expectations do not reuse the application's own date arithmetic.
FROZEN_DATE = "2026-08-31"
WINDOW_CUTOFFS = {
    "last30days": "2026-08-01",
    "last6months": "2026-02-28",
    "lastyear": "2025-08-31",
}
WINDOW_BOUNDARY_TITLES = {
    "last30days": ("Thirty Day Mark", "Just Past Thirty Days"),
    "last6months": ("Six Month Mark", "Just Past Six Months"),
    "lastyear": ("One Year Mark", "Just Past One Year"),
}


@pytest.fixture(scope="module")
def seed(frozen_today):
    """Expected data, derived from the seed definition and independent of the app's filter code."""
    assert frozen_today.isoformat() == FROZEN_DATE
    return [dict(zip(SEED_COLUMNS, row)) for row in build_books(frozen_today)]


@pytest.fixture
def home(page: Page, seed):
    page.goto("/")
    expect(cards(page)).to_have_count(len(seed))
    return page


def cards(page: Page):
    return page.get_by_test_id("book-card")


def card_titles(page: Page):
    return cards(page).get_by_role("heading", level=3)


def category_tab(page: Page, name: str):
    return page.get_by_role("button", name=f"{name} Books", exact=True)


def filter_control(page: Page, label: str):
    return page.get_by_label(label)


def titles_of(books):
    return [book["title"] for book in books]


def expect_results(page: Page, expected):
    """Wait until the rendered cards match the expected books (the API lists books in seed order)."""
    expect(card_titles(page)).to_have_text(titles_of(expected))


def open_category(page: Page, name: str):
    category_tab(page, name).click()
    expect(page.locator("#section-title")).to_have_text(f"{name} Books")


def apply_filters(page: Page, **selections):
    for label, value in selections.items():
        filter_control(page, label.replace("_", " ")).select_option(value)


def in_category(seed, category):
    return [book for book in seed if book["category"] == category]


def non_fiction(seed):
    return in_category(seed, "Non-Fiction")


def published_since(books, window):
    return [b for b in books if b["publication_date"] >= WINDOW_CUTOFFS[window]]


def test_category_controls_are_available(home):
    expect(category_tab(home, "Fiction")).to_be_visible()
    expect(category_tab(home, "Non-Fiction")).to_be_visible()


def test_non_fiction_shows_all_four_filter_groups(home):
    open_category(home, "Non-Fiction")
    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_be_visible()
    expect(filter_control(home, "Book Format").locator("option")).to_have_text(
        ["Any", "Hardcover", "Paperback", "eBook", "Audiobook"])
    expect(filter_control(home, "Language").locator("option")).to_have_text(
        ["Any", "English", "Spanish", "French", "German"])
    expect(filter_control(home, "Publication Date").locator("option")).to_have_text(
        ["Any time", "Last 30 days", "Last 6 months", "Last year"])
    expect(filter_control(home, "Customer Reviews").locator("option")).to_have_text(
        ["Any rating", "3 stars and above", "4 stars and above"])


def test_single_filter_language(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Language").select_option("English")
    expected = [b for b in non_fiction(seed) if b["language"] == "English"]
    assert expected
    expect_results(home, expected)


def test_multiple_filters_format_and_language(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Book Format").select_option("hardcover")
    filter_control(home, "Language").select_option("English")
    expected = [b for b in non_fiction(seed)
                if b["format"] == "hardcover" and b["language"] == "English"]
    assert expected
    expect_results(home, expected)


def test_minimum_rating_four_stars(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Customer Reviews").select_option("4")
    expected = [b for b in non_fiction(seed) if b["customer_rating"] >= 4]
    assert expected
    expect_results(home, expected)


def test_minimum_rating_three_stars(home, seed):
    open_category(home, "Fiction")
    filter_control(home, "Customer Reviews").select_option("3")
    expected = [b for b in in_category(seed, "Fiction") if b["customer_rating"] >= 3]
    assert expected and len(expected) < len(in_category(seed, "Fiction"))
    expect_results(home, expected)


@pytest.mark.parametrize("window", list(WINDOW_CUTOFFS))
def test_publication_date_window_non_fiction_includes_boundary_book(home, seed, window):
    inside, outside = WINDOW_BOUNDARY_TITLES[window]
    open_category(home, "Non-Fiction")
    filter_control(home, "Publication Date").select_option(window)
    expected = published_since(non_fiction(seed), window)
    assert inside in titles_of(expected) and outside not in titles_of(expected)
    expect_results(home, expected)
    expect(card_titles(home).filter(has_text=re.compile(f"^{re.escape(inside)}$"))).to_have_count(1)
    expect(card_titles(home).filter(has_text=re.compile(f"^{re.escape(outside)}$"))).to_have_count(0)


@pytest.mark.parametrize("window", list(WINDOW_CUTOFFS))
def test_publication_date_window_fiction(home, seed, window):
    open_category(home, "Fiction")
    filter_control(home, "Publication Date").select_option(window)
    fiction = in_category(seed, "Fiction")
    expected = published_since(fiction, window)
    assert expected
    expect_results(home, expected)


def test_publication_date_windows_are_nested(home, seed):
    open_category(home, "Non-Fiction")
    counts = {}
    for window in WINDOW_CUTOFFS:
        filter_control(home, "Publication Date").select_option(window)
        expected = published_since(non_fiction(seed), window)
        expect_results(home, expected)
        counts[window] = len(expected)
    assert counts["last30days"] < counts["last6months"] < counts["lastyear"]


@pytest.mark.parametrize("category", CATEGORY_NAMES)
def test_clear_filters_resets_filters_and_keeps_category(home, seed, category):
    open_category(home, category)
    apply_filters(home, Book_Format="hardcover", Language="English",
                  Publication_Date="lastyear", Customer_Reviews="4")
    filtered = [b for b in published_since(in_category(seed, category), "lastyear")
                if b["format"] == "hardcover" and b["language"] == "English"
                and b["customer_rating"] >= 4]
    assert filtered and len(filtered) < len(in_category(seed, category))
    expect_results(home, filtered)

    home.get_by_role("button", name="Clear Filters").click()

    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_have_value("")
    expect(category_tab(home, category)).to_have_class(re.compile(r"\bactive\b"))
    expect(home.locator("#section-title")).to_have_text(f"{category} Books")
    expect_results(home, in_category(seed, category))


@pytest.mark.parametrize("source,target", [("Fiction", "Non-Fiction"), ("Non-Fiction", "Fiction")])
def test_filters_persist_when_switching_category(home, seed, source, target):
    open_category(home, source)
    apply_filters(home, Book_Format="hardcover", Language="Spanish", Customer_Reviews="3")

    def matching(category):
        return [b for b in in_category(seed, category) if b["format"] == "hardcover"
                and b["language"] == "Spanish" and b["customer_rating"] >= 3]

    assert matching(source) and matching(target)
    expect_results(home, matching(source))

    open_category(home, target)

    expect(filter_control(home, "Book Format")).to_have_value("hardcover")
    expect(filter_control(home, "Language")).to_have_value("Spanish")
    expect(filter_control(home, "Customer Reviews")).to_have_value("3")
    expect(filter_control(home, "Publication Date")).to_have_value("")
    expect_results(home, matching(target))


def test_filters_work_the_same_in_fiction_and_non_fiction(home, seed):
    open_category(home, "Fiction")
    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_be_visible()
    filter_control(home, "Language").select_option("Spanish")
    fiction = [b for b in in_category(seed, "Fiction") if b["language"] == "Spanish"]
    assert fiction
    expect_results(home, fiction)

    open_category(home, "Non-Fiction")
    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_be_visible()
    expect(filter_control(home, "Language")).to_have_value("Spanish")
    nonfiction = [b for b in non_fiction(seed) if b["language"] == "Spanish"]
    assert nonfiction
    expect_results(home, nonfiction)


def test_no_results_state_and_recovery(home, seed):
    open_category(home, "Fiction")
    apply_filters(home, Book_Format="audiobook", Language="German")
    assert not [b for b in in_category(seed, "Fiction")
                if b["format"] == "audiobook" and b["language"] == "German"]

    expect(home.get_by_text("No books found.")).to_be_visible()
    expect(cards(home)).to_have_count(0)
    expect(home.locator("#section-title")).to_have_text("Fiction Books")

    home.get_by_role("button", name="Clear Filters").click()

    expect(home.get_by_text("No books found.")).to_have_count(0)
    expect_results(home, in_category(seed, "Fiction"))
