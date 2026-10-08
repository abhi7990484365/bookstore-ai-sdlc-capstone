@EPMCDMETST-68481
Feature: Advanced book filtering for Non-Fiction and Fiction
  As a bookstore customer
  I want to narrow the book list by format, language, publication date and customer reviews
  So that I can find Non-Fiction books the same way I find Fiction books

  # Filter semantics
  #   - Filters combine with AND logic.
  #   - Publication windows are inclusive of the cutoff date (on or after the cutoff).
  #   - Customer Reviews is a minimum rating, inclusive (4 = 4.0 and above, 3 = 3.0 and above).
  #   - An empty filter value means "no filter".
  #   - Invalid non-empty values are rejected by the API with HTTP 400 and a string "detail".
  #   - Clear Filters resets the four advanced filters and keeps the selected category.
  #   - Filter selections persist when the customer switches category.
  #
  # Tags: @ui = Playwright browser scenario, @api = pytest API scenario.

  Background:
    Given the bookstore is seeded with Fiction and Non-Fiction books
    And the current date is fixed at "2026-08-31"

  # ---------------------------------------------------------------------------
  # Non-Fiction category and filter controls
  # ---------------------------------------------------------------------------

  @ui @non-fiction
  Scenario: Non-Fiction shows all four filter groups with the approved options
    When I open the "Non-Fiction" category
    Then I see the filter groups "Book Format", "Language", "Publication Date" and "Customer Reviews"
    And "Book Format" offers "Any", "Hardcover", "Paperback", "eBook" and "Audiobook"
    And "Language" offers "Any", "English", "Spanish", "French" and "German"
    And "Publication Date" offers "Any time", "Last 30 days", "Last 6 months" and "Last year"
    And "Customer Reviews" offers "Any rating", "3 stars and above" and "4 stars and above"

  @api @non-fiction
  Scenario: Non-Fiction category returns only Non-Fiction books
    When I request books with category "Non-Fiction"
    Then the response status is 200
    And every returned book has category "Non-Fiction"

  # ---------------------------------------------------------------------------
  # Book Format filter - single filter
  # ---------------------------------------------------------------------------

  @api @format
  Scenario Outline: Filter Non-Fiction and Fiction books by Book Format
    When I request books with category "<category>" and format "<format>"
    Then the response status is 200
    And at least one book is returned
    And every returned book has category "<category>" and format "<format>"
    And no matching "<category>" book with format "<format>" is missing from the result

    Examples:
      | category    | format    |
      | Non-Fiction | hardcover |
      | Non-Fiction | paperback |
      | Non-Fiction | eBook     |
      | Non-Fiction | audiobook |
      | Fiction     | hardcover |
      | Fiction     | paperback |
      | Fiction     | eBook     |
      | Fiction     | audiobook |

  @ui @format
  Scenario: Select a Book Format in the browser (Non-Fiction)
    Given I open the "Non-Fiction" category
    When I select Book Format "hardcover"
    Then only Non-Fiction books with format "hardcover" are listed

  # ---------------------------------------------------------------------------
  # Language filter - single filter
  # ---------------------------------------------------------------------------

  @api @language
  Scenario Outline: Filter Non-Fiction and Fiction books by Language
    When I request books with category "<category>" and language "<language>"
    Then the response status is 200
    And at least one book is returned
    And every returned book has category "<category>" and language "<language>"
    And no matching "<category>" book in "<language>" is missing from the result

    Examples:
      | category    | language |
      | Non-Fiction | English  |
      | Non-Fiction | Spanish  |
      | Non-Fiction | French   |
      | Non-Fiction | German   |
      | Fiction     | English  |
      | Fiction     | Spanish  |
      | Fiction     | French   |
      | Fiction     | German   |

  @ui @language @single-filter
  Scenario: Select a single Language in the browser (Non-Fiction)
    Given I open the "Non-Fiction" category
    When I select Language "English"
    Then only Non-Fiction books in "English" are listed

  # ---------------------------------------------------------------------------
  # Publication Date filter - single filter
  # ---------------------------------------------------------------------------

  @api @publication-date
  Scenario Outline: Filter by Publication Date window
    When I request books with category "<category>" and publicationDate "<window>"
    Then the response status is 200
    And at least one book is returned
    And every returned book was published on or after "<cutoff>"
    And no book published on or after "<cutoff>" in that category is missing from the result

    Examples:
      | category    | window      | cutoff     |
      | Non-Fiction | last30days  | 2026-08-01 |
      | Non-Fiction | last6months | 2026-02-28 |
      | Non-Fiction | lastyear    | 2025-08-31 |
      | Fiction     | last30days  | 2026-08-01 |
      | Fiction     | last6months | 2026-02-28 |
      | Fiction     | lastyear    | 2025-08-31 |

  @api @ui @publication-date @boundary
  Scenario Outline: Publication Date cutoff is inclusive
    Given a Non-Fiction book "<inside>" published exactly on the "<window>" cutoff date
    And a Non-Fiction book "<outside>" published one day before the cutoff date
    When I filter Non-Fiction books by Publication Date "<window>"
    Then "<inside>" is listed
    And "<outside>" is not listed

    Examples:
      | window      | inside          | outside               |
      | last30days  | Thirty Day Mark | Just Past Thirty Days |
      | last6months | Six Month Mark  | Just Past Six Months  |
      | lastyear    | One Year Mark   | Just Past One Year    |

  @api @ui @publication-date
  Scenario: Publication Date windows are nested
    When I filter Non-Fiction books by "last30days", "last6months" and "lastyear"
    Then the "last30days" result is a strict subset of the "last6months" result
    And the "last6months" result is a strict subset of the "lastyear" result

  @api @publication-date
  Scenario: Six months back from a month-end date is clamped to the last day of the shorter month
    Given today is "2026-08-31"
    When the "last6months" cutoff is calculated
    Then the cutoff is "2026-02-28"

  # ---------------------------------------------------------------------------
  # Customer Reviews filter - single filter
  # ---------------------------------------------------------------------------

  @api @reviews
  Scenario Outline: Filter by minimum Customer Reviews rating
    When I request books with category "<category>" and minRating "<stars>"
    Then the response status is 200
    And at least one book is returned
    And every returned book has a customer rating of <stars>.0 or higher
    And no book in that category rated <stars>.0 or higher is missing from the result

    Examples:
      | category    | stars |
      | Non-Fiction | 4     |
      | Non-Fiction | 3     |
      | Fiction     | 4     |
      | Fiction     | 3     |

  @api @reviews @boundary
  Scenario: Minimum rating boundaries are inclusive
    When I request books with minRating "3" and with minRating "4"
    Then "Midnight Echoes" (rated 3.0) is in the "3 stars and above" result
    And "Midnight Echoes" is not in the "4 stars and above" result
    And "Cold Harbor" (rated 4.0) is in the "4 stars and above" result
    And "Der Letzte Zug" (rated 2.9) is in neither result

  @ui @reviews
  Scenario: Select 4 stars and above in the browser (Non-Fiction)
    Given I open the "Non-Fiction" category
    When I select Customer Reviews "4 stars and above"
    Then only Non-Fiction books rated 4.0 or higher are listed

  @ui @reviews
  Scenario: Select 3 stars and above in the browser (Fiction)
    Given I open the "Fiction" category
    When I select Customer Reviews "3 stars and above"
    Then only Fiction books rated 3.0 or higher are listed
    And fewer books are listed than in the unfiltered Fiction category

  # ---------------------------------------------------------------------------
  # Multiple filters - AND logic
  # ---------------------------------------------------------------------------

  @ui @multiple-filters
  Scenario: Book Format and Language combine with AND in the browser
    Given I open the "Non-Fiction" category
    When I select Book Format "hardcover"
    And I select Language "English"
    Then only Non-Fiction books that are "hardcover" AND "English" are listed

  @api @multiple-filters
  Scenario: All four filters combine with AND (documented example)
    When I request books with category "Non-Fiction", format "hardcover", publicationDate "lastyear" and minRating "4"
    Then the response status is 200
    And exactly one book is returned: "History of Modern Cities"

  @api @multiple-filters
  Scenario Outline: Four filters together return only books that match every filter
    When I request books with category "<category>", format "paperback", language "English", publicationDate "lastyear" and minRating "4"
    Then the result contains exactly the "<category>" books that are paperback AND English AND published on or after "2025-08-31" AND rated 4.0 or higher

    Examples:
      | category    |
      | Non-Fiction |
      | Fiction     |

  @api @multiple-filters
  Scenario: Adding a filter narrows the result
    Given Non-Fiction filtered by language "English" returns N books
    When I also filter by format "hardcover"
    Then fewer than N books are returned
    And every returned book was in the language-only result

  # ---------------------------------------------------------------------------
  # Clear filters while preserving category
  # ---------------------------------------------------------------------------

  @ui @clear-filters
  Scenario Outline: Clear Filters resets all filters and keeps the selected category
    Given I open the "<category>" category
    And I select Book Format "hardcover", Language "English", Publication Date "lastyear" and Customer Reviews "4 stars and above"
    And fewer books are listed than in the unfiltered "<category>" category
    When I click "Clear Filters"
    Then "Book Format", "Language", "Publication Date" and "Customer Reviews" show their default "Any" value
    And the "<category>" tab is still active
    And the heading reads "<category> Books"
    And all "<category>" books are listed
    And no books from the other category are listed

    Examples:
      | category    |
      | Fiction     |
      | Non-Fiction |

  @api @clear-filters
  Scenario Outline: Requesting the category without filters restores the full category list
    Given I requested "<category>" books with format "hardcover" and minRating "4"
    When I request books with category "<category>" only
    Then the result contains every "<category>" book
    And the filtered result was a strict subset of this result

    Examples:
      | category    |
      | Fiction     |
      | Non-Fiction |

  # ---------------------------------------------------------------------------
  # Fiction and Non-Fiction behavior
  # ---------------------------------------------------------------------------

  @ui @parity
  Scenario: Fiction and Non-Fiction expose the same filters and behave the same way
    Given I open the "Fiction" category
    Then I see the filter groups "Book Format", "Language", "Publication Date" and "Customer Reviews"
    When I select Language "Spanish"
    Then only Fiction books in "Spanish" are listed
    When I open the "Non-Fiction" category
    Then I see the filter groups "Book Format", "Language", "Publication Date" and "Customer Reviews"
    And Language is still "Spanish"
    And only Non-Fiction books in "Spanish" are listed

  @ui @parity
  Scenario Outline: Filter selections persist when switching category
    Given I open the "<from>" category
    And I select Book Format "hardcover", Language "Spanish" and Customer Reviews "3 stars and above"
    When I open the "<to>" category
    Then Book Format is still "hardcover"
    And Language is still "Spanish"
    And Customer Reviews is still "3 stars and above"
    And Publication Date is still "Any time"
    And only "<to>" books that are hardcover, Spanish and rated 3.0 or higher are listed

    Examples:
      | from        | to          |
      | Fiction     | Non-Fiction |
      | Non-Fiction | Fiction     |

  @api @parity
  Scenario Outline: The same filter value selects matching books in both categories
    When I request books with category "Fiction" and <filter>
    And I request books with category "Non-Fiction" and <filter>
    Then each result equals the books of its own category that match <filter>

    Examples:
      | filter                                                  |
      | format "hardcover"                                      |
      | language "Spanish"                                      |
      | publicationDate "last6months"                           |
      | minRating "4"                                           |
      | format "hardcover", language "Spanish" and minRating "4" |

  @api @regression
  Scenario: Category behavior without advanced filters is unchanged
    When I request all books
    Then both "Fiction" and "Non-Fiction" books are returned
    When I request books with category "Fiction"
    Then every returned book has category "Fiction"
    When I request books with category "Non-Fiction"
    Then every returned book has category "Non-Fiction"
    When I request books with category "Unknown"
    Then the response status is 400

  @api @regression
  Scenario: Empty filter values mean no filter
    When I request books with category "", format "", language "", publicationDate "" and minRating ""
    Then the result equals the result of requesting all books

  # ---------------------------------------------------------------------------
  # Invalid format
  # ---------------------------------------------------------------------------

  @api @negative @format
  Scenario Outline: Invalid format is rejected
    When I request books with format "<value>"
    Then the response status is 400
    And the response "detail" is a text message

    Examples:
      | value        |
      | pdf          |
      | ebook        |
      | EBOOK        |
      | Hardcover    |
      | " hardcover" |
      | "hardcover " |
      | x            |

  @api @negative @format
  Scenario Outline: Invalid format is rejected within a category
    When I request books with category "<category>" and format "pdf"
    Then the response status is 400

    Examples:
      | category    |
      | Fiction     |
      | Non-Fiction |

  @api @format
  Scenario Outline: Every valid format is accepted with its exact spelling
    When I request books with format "<value>"
    Then the response status is 200
    And every returned book has format "<value>"

    Examples:
      | value     |
      | hardcover |
      | paperback |
      | eBook     |
      | audiobook |

  # ---------------------------------------------------------------------------
  # Invalid language
  # ---------------------------------------------------------------------------

  @api @negative @language
  Scenario Outline: Invalid language is rejected
    When I request books with language "<value>"
    Then the response status is 400
    And the response "detail" is a text message

    Examples:
      | value      |
      | Klingon    |
      | english    |
      | ENGLISH    |
      | " English" |
      | "English " |
      | x          |

  @api @negative @language
  Scenario Outline: Invalid language is rejected within a category
    When I request books with category "<category>" and language "Klingon"
    Then the response status is 400

    Examples:
      | category    |
      | Fiction     |
      | Non-Fiction |

  @api @language
  Scenario Outline: Every valid language is accepted with its exact spelling
    When I request books with language "<value>"
    Then the response status is 200
    And every returned book has language "<value>"

    Examples:
      | value   |
      | English |
      | Spanish |
      | French  |
      | German  |

  # ---------------------------------------------------------------------------
  # Invalid rating (and other invalid values)
  # ---------------------------------------------------------------------------

  @api @negative @reviews
  Scenario Outline: Invalid minimum rating is rejected
    When I request books with minRating "<value>"
    Then the response status is 400
    And the response "detail" is a text message

    Examples:
      | value |
      | abc   |
      | 3.5   |
      | 0     |
      | -1    |
      | 2     |
      | 5     |

  @api @negative @publication-date
  Scenario: Invalid publication window is rejected
    When I request books with publicationDate "lastcentury"
    Then the response status is 400

  @api @negative
  Scenario: An invalid value is rejected even when other filters are valid
    When I request books with category "Fiction", format "hardcover" and minRating "abc"
    Then the response status is 400

  @api @negative @security
  Scenario: SQL injection style values are rejected and data is unchanged
    Given I note the full book list
    When I request books with format "x' OR '1'='1"
    Then the response status is 400
    When I request books with language "x'; DROP TABLE books;--"
    Then the response status is 400
    And the full book list is unchanged

  # ---------------------------------------------------------------------------
  # Empty / no-results and recovery
  # ---------------------------------------------------------------------------

  @api @no-results
  Scenario: A combination with no matches returns an empty list
    When I request books with category "Fiction", format "audiobook" and language "German"
    Then the response status is 200
    And the result is an empty list

  @ui @no-results @clear-filters
  Scenario: No-results message is shown and the list recovers after Clear Filters
    Given I open the "Fiction" category
    When I select Book Format "audiobook"
    And I select Language "German"
    Then the message "No books found." is shown
    And no book cards are listed
    And the heading still reads "Fiction Books"
    When I click "Clear Filters"
    Then the message "No books found." is no longer shown
    And all Fiction books are listed
