// static/return_book_logic.js

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('resultsTableBody');
    const allRows = Array.from(tableBody.querySelectorAll('tr'));

    function filterTable() {
        const query = searchInput.value.toLowerCase();

        allRows.forEach(row => {
            const bookTitle = row.querySelector('.book-title').textContent.toLowerCase();
            const bookAuthor = row.querySelector('.book-author').textContent.toLowerCase();
            const readerName = row.querySelector('.reader-name').textContent.toLowerCase();
            const invNumber = row.querySelector('.inv-number').textContent.toLowerCase();
            
            if (bookTitle.includes(query) || bookAuthor.includes(query) || readerName.includes(query) || invNumber.includes(query)) {
                row.style.display = ''; // Показваме реда, ако има съвпадение
            } else {
                row.style.display = 'none'; // Скриваме реда, ако няма
            }
        });
    }

    searchInput.addEventListener('keyup', filterTable);
});