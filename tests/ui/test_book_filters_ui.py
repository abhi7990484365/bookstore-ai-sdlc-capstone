import re
import pytest
from playwright.sync_api import Page, expect
from scripts.seed import build_books

FILTER_LABELS = ["Book Format", "Language", "Publication Date", "Customer Reviews"]
SEED_COLUMNS = ("title", "author", "category", "format", "language",
                "publication_date", "customer_rating", "price")


@pytest.fixture(scope="module")
def seed(frozen_today):
    """Expected data, derived from the seed definition and independent of the app's filter code."""
    return [dict(zip(SEED_COLUMNS, row)) for row in build_books(frozen_today)]


@pytest.fixture
def home(page: Page, seed):
    page.goto("/")
    expect(cards(page)).to_have_count(len(seed))
    return page


def cards(page: Page):
    return page.get_by_test_id("book-card")


def category_tab(page: Page, name: str):
    return page.get_by_role("button", name=f"{name} Books", exact=True)


def filter_control(page: Page, label: str):
    return page.get_by_label(label)


def titles_of(books):
    return {book["title"] for book in books}


def displayed_books(page: Page):
    """Read the rendered cards (the UI's own view of the results)."""
    books = []
    for text in cards(page).all_inner_texts():
        fields = dict(re.findall(r"^(\w+): (.*)$", text, flags=re.MULTILINE))
        books.append({
            "title": text.splitlines()[0],
            "category": fields["Category"],
            "format": fields["Format"],
            "language": fields["Language"],
            "publication_date": fields["Published"],
            "customer_rating": float(fields["Rating"]),
        })
    return books


def expect_results(page: Page, expected):
    expect(cards(page)).to_have_count(len(expected))
    shown = displayed_books(page)
    assert titles_of(shown) == titles_of(expected)
    return shown


def open_category(page: Page, name: str):
    category_tab(page, name).click()
    expect(page.locator("#section-title")).to_have_text(f"{name} Books")


def non_fiction(seed):
    return [book for book in seed if book["category"] == "Non-Fiction"]


def one_year_ago(today):
    return today.replace(year=today.year - 1).isoformat()


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
    shown = expect_results(home, expected)
    assert shown
    assert all(b["language"] == "English" and b["category"] == "Non-Fiction" for b in shown)


def test_multiple_filters_format_and_language(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Book Format").select_option("hardcover")
    filter_control(home, "Language").select_option("English")
    expected = [b for b in non_fiction(seed)
                if b["format"] == "hardcover" and b["language"] == "English"]
    shown = expect_results(home, expected)
    assert shown
    assert all(b["format"] == "hardcover" and b["language"] == "English" for b in shown)


def test_minimum_rating_four_stars(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Customer Reviews").select_option("4")
    expected = [b for b in non_fiction(seed) if b["customer_rating"] >= 4]
    shown = expect_results(home, expected)
    assert shown
    assert all(b["customer_rating"] >= 4 for b in shown)


def test_publication_date_last_year(home, seed, frozen_today):
    open_category(home, "Non-Fiction")
    filter_control(home, "Publication Date").select_option("lastyear")
    cutoff = one_year_ago(frozen_today)
    expected = [b for b in non_fiction(seed) if b["publication_date"] >= cutoff]
    shown = expect_results(home, expected)
    assert all(b["publication_date"] >= cutoff for b in shown)
    assert "One Year Mark" in titles_of(shown)
    assert "Just Past One Year" not in titles_of(shown)


def test_clear_filters_resets_filters_and_keeps_category(home, seed):
    open_category(home, "Non-Fiction")
    filter_control(home, "Book Format").select_option("hardcover")
    filter_control(home, "Language").select_option("English")
    filter_control(home, "Customer Reviews").select_option("4")
    filtered = [b for b in non_fiction(seed) if b["format"] == "hardcover"
                and b["language"] == "English" and b["customer_rating"] >= 4]
    expect_results(home, filtered)

    home.get_by_role("button", name="Clear Filters").click()

    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_have_value("")
    expect(category_tab(home, "Non-Fiction")).to_have_class(re.compile(r"\bactive\b"))
    expect(home.locator("#section-title")).to_have_text("Non-Fiction Books")
    shown = expect_results(home, non_fiction(seed))
    assert all(b["category"] == "Non-Fiction" for b in shown)


def test_filters_work_the_same_in_fiction_and_non_fiction(home, seed):
    open_category(home, "Fiction")
    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_be_visible()
    filter_control(home, "Language").select_option("Spanish")
    fiction = [b for b in seed if b["category"] == "Fiction" and b["language"] == "Spanish"]
    shown = expect_results(home, fiction)
    assert shown and all(b["category"] == "Fiction" and b["language"] == "Spanish" for b in shown)

    open_category(home, "Non-Fiction")
    for label in FILTER_LABELS:
        expect(filter_control(home, label)).to_be_visible()
    expect(filter_control(home, "Language")).to_have_value("Spanish")
    nonfiction = [b for b in non_fiction(seed) if b["language"] == "Spanish"]
    shown = expect_results(home, nonfiction)
    assert shown and all(b["category"] == "Non-Fiction" and b["language"] == "Spanish" for b in shown)
