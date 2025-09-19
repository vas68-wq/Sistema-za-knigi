document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('resultsTableBody');
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
        // Добавяме индикатор за зареждане
        tableBody.innerHTML = '<tr><td colspan="6" class="no-data">Търсене...</td></tr>';

        fetch(`/api/search_books?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                updateTable(data);
            })
            .catch(error => {
                console.error('Грешка при търсене:', error);
                tableBody.innerHTML = '<tr><td colspan="6" class="no-data">Възникна грешка при търсенето.</td></tr>';
            });
    }

    function updateTable(books) {
        tableBody.innerHTML = '';
        if (books.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="no-data">Няма намерени книги.</td></tr>';
            return;
        }

        books.forEach(book => {
            const row = `
                <tr>
                    <td>${book.tom_no}</td>
                    <td>${book.title}</td>
                    <td>${book.author}</td>
                    <td>${book.genre || ''}</td>
                    <td>${book.publish_year || ''}</td>
                    <td>
                        <a href="/edit_book/${book.tom_no}" class="btn-edit">Редактирай</a>
                        <form action="/delete_book/${book.tom_no}" method="POST" style="display:inline;">
                            <button type="submit" class="btn-delete" onclick="return confirm('Сигурни ли сте?');">Изтрий</button>
                        </form>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    }

    const debouncedSearch = debounce(performSearch, 300);
    searchInput.addEventListener('keyup', debouncedSearch);
    
    performSearch(); // Първоначално зареждане
});