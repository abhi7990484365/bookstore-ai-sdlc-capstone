const list = document.getElementById("book-list");
const title = document.getElementById("section-title");
const error = document.getElementById("error");

const FILTER_KEYS = ["format", "language", "publicationDate", "minRating"];
const state = { category: "", format: "", language: "", publicationDate: "", minRating: "" };

function buildUrl() {
  const params = new URLSearchParams();
  ["category", ...FILTER_KEYS].forEach(key => {
    if (state[key]) params.set(key, state[key]);
  });
  const query = params.toString();
  return query ? `/api/books?${query}` : "/api/books";
}

async function loadBooks() {
  error.hidden = true;
  list.innerHTML = "<p>Loading...</p>";
  try {
    const response = await fetch(buildUrl());
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const books = await response.json();
    title.textContent = state.category ? `${state.category} Books` : "All Books";
    if (!books.length) {
      list.innerHTML = "<p>No books found.</p>";
      return;
    }
    list.innerHTML = books.map(book => `
      <article class="book-card" data-testid="book-card">
        <h3>${escapeHtml(book.title)}</h3>
        <p><strong>Author:</strong> ${escapeHtml(book.author)}</p>
        <p><strong>Category:</strong> ${escapeHtml(book.category)}</p>
        <p><strong>Format:</strong> ${escapeHtml(book.format)}</p>
        <p><strong>Language:</strong> ${escapeHtml(book.language)}</p>
        <p><strong>Published:</strong> ${escapeHtml(book.publication_date)}</p>
        <p><strong>Rating:</strong> ${book.customer_rating}</p>
        <p><strong>Price:</strong> $${book.price.toFixed(2)}</p>
      </article>`).join("");
  } catch (e) {
    list.innerHTML = "";
    error.textContent = "Unable to load books. Please try again.";
    error.hidden = false;
    console.error(e);
  }
}

function escapeHtml(value) {
  return String(value).replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    state.category = tab.dataset.category;
    loadBooks();
  });
});

FILTER_KEYS.forEach(key => {
  document.getElementById(`filter-${key}`).addEventListener("change", event => {
    state[key] = event.target.value;
    loadBooks();
  });
});

document.getElementById("clear-filters").addEventListener("click", () => {
  FILTER_KEYS.forEach(key => {
    state[key] = "";
    document.getElementById(`filter-${key}`).value = "";
  });
  loadBooks();
});

loadBooks();
