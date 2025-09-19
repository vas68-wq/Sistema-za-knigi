document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const genreSelect = document.getElementById('genreSelect');
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsCount = document.getElementById('resultsCount');
    let debounceTimer;

    function debounce(func, delay) {
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(context, args), delay);
        };
    }

    function performSearch() {
        const query = searchInput.value;
        const genre = genreSelect.value;

        if (query.length < 3 && genre === "") {
            resultsContainer.innerHTML = '<p class="no-data">Моля, въведете поне 3 символа в полето за търсене или изберете жанр.</p>';
            resultsCount.textContent = '';
            return;
        }

        resultsContainer.innerHTML = '<p class="no-data">Търсене...</p>';

        fetch(`/api/public_search_books?query=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}`)
            .then(response => response.json())
            .then(data => {
                updateResults(data);
            })
            .catch(error => {
                console.error('Грешка при търсене:', error);
                resultsContainer.innerHTML = '<p class="no-data">Възникна грешка при търсенето.</p>';
            });
    }

    function updateResults(books) {
        resultsContainer.innerHTML = '';
        resultsCount.textContent = `Намерени са ${books.length} резултата`;

        if (books.length === 0) {
            resultsContainer.innerHTML += '<p class="no-data">Няма намерени книги, отговарящи на Вашето търсене.</p>';
            return;
        }

        books.forEach(book => {
            let copiesHtml = '';
            book.copies.forEach((copy, index) => {
                copiesHtml += `<strong>${copy.inventory_number}</strong>`;
                if (copy.status === 'Заета') {
                    copiesHtml += ` (заета до ${copy.due_date || 'N/A'})`;
                }
                if (index < book.copies.length - 1) {
                    copiesHtml += ', ';
                }
            });

            let availableCopies = book.copies.filter(c => c.status === 'Налична').length;
            let totalCopies = book.copies.length;
            let statusHtml = '';

            if (availableCopies > 0) {
                if (totalCopies === 1) {
                    statusHtml = '<div class="status available">Налична</div>';
                } else {
                    statusHtml = '<div class="status available">Има налични</div>';
                }
            } else {
                if (totalCopies === 1) {
                    statusHtml = '<div class="status taken">Заета</div>';
                } else {
                    statusHtml = '<div class="status taken">Всички заети</div>';
                }
            }

            const bookEntry = `
                <div class="book-entry">
                    <div class="book-info">
                        <h3>${book.title}</h3>
                        <p>Автор: ${book.author}</p>
                        <p class="inventory-numbers">Инв. номер: ${copiesHtml}</p>
                    </div>
                    ${statusHtml}
                </div>
            `;
            resultsContainer.innerHTML += bookEntry;
        });
    }

    const debouncedSearch = debounce(performSearch, 400);
    searchInput.addEventListener('keyup', debouncedSearch);
    genreSelect.addEventListener('change', performSearch);
});