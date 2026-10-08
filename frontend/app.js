const list = document.getElementById("book-list");
const title = document.getElementById("section-title");
const error = document.getElementById("error");

async function loadBooks(category = "") {
  error.hidden = true;
  list.innerHTML = "<p>Loading...</p>";
  const url = category ? `/api/books?category=${encodeURIComponent(category)}` : "/api/books";
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const books = await response.json();
    title.textContent = category ? `${category} Books` : "All Books";
    if (!books.length) {
      list.innerHTML = "<p>No books found.</p>";
      return;
    }
    list.innerHTML = books.map(book => `
      <article class="book-card">
        <h3>${escapeHtml(book.title)}</h3>
        <p><strong>Author:</strong> ${escapeHtml(book.author)}</p>
        <p><strong>Category:</strong> ${escapeHtml(book.category)}</p>
        <p><strong>Format:</strong> ${escapeHtml(book.format)}</p>
        <p><strong>Language:</strong> ${escapeHtml(book.language)}</p>
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
    loadBooks(tab.dataset.category);
  });
});

loadBooks();
