document.addEventListener('DOMContentLoaded', function () {
    // Елементи, които съществуват само на страницата със списъка
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const tableContainer = document.getElementById('books-table-container');
    const paginationContainer = document.getElementById('pagination-container');
    const totalBooksCount = document.getElementById('totalBooksCount');
    const loadingSpinner = document.getElementById('loading-spinner');

    let currentPage = 1;
    let currentQuery = '';
    let debounceTimer;
    let allGenres = []; // Ще пазим жанровете тук, за да не ги зареждаме всеки път

    // --- Функции, специфични за СПИСЪКА С КНИГИ ---
    async function fetchBooks(page = 1, query = '') {
        if (!loadingSpinner || !tableContainer) return; // Спираме, ако не сме на страницата със списъка
        
        loadingSpinner.style.display = 'block';
        tableContainer.innerHTML = '';
        try {
            currentPage = page;
            currentQuery = query;

            const response = await fetch(`/api/books?page=${page}&query=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            allGenres = data.genres; // Запазваме жанровете
            renderTable(data.books);
            renderPagination(data.pagination);
            updateTotalBooksCount(data.pagination.total_books);
            populateGenreDatalists(allGenres);
        } catch (error) {
            console.error('Fetch error:', error);
            tableContainer.innerHTML = '<p class="text-danger">Грешка при зареждане на книгите.</p>';
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    function renderTable(books) {
        if (!tableContainer) return;
        if (books.length === 0) {
            tableContainer.innerHTML = '<p>Няма намерени книги.</p>';
            return;
        }

        const backUrl = encodeURIComponent(`/books?page=${currentPage}&query=${encodeURIComponent(currentQuery)}`);
        let tableBodyHtml = '';
        books.forEach(book => {
            const availability = book.is_borrowed ? '<span class="badge bg-warning text-dark">Заета</span>' : '<span class="badge bg-success">Налична</span>';
            const detailUrl = `/book/${book.tom_no}?back_url=${backUrl}`;
            tableBodyHtml += `
                <tr>
                    <td>${book.tom_no}</td>
                    <td><a href="${detailUrl}">${book.title}</a></td>
                    <td>${book.author}</td>
                    <td>${book.genre || ''}</td>
                    <td>${book.publish_year || ''}</td>
                    <td>${availability}</td>
                    <td class="d-flex flex-nowrap">
                        <button class="btn btn-sm btn-outline-primary edit-book-btn" 
                                data-bs-toggle="modal" 
                                data-bs-target="#editBookModal" 
                                data-book-id="${book.tom_no}">
                            <i class="fas fa-edit"></i> Редактирай
                        </button>
                        <form action="/delete_book/${book.tom_no}" method="POST" class="d-inline ms-1" onsubmit="return confirm('Сигурни ли сте, че искате да изтриете тази книга?');">
                            <button type="submit" class="btn btn-sm btn-outline-danger">
                                <i class="fas fa-trash"></i> Изтрий
                            </button>
                        </form>
                    </td>
                </tr>
            `;
        });
        tableContainer.innerHTML = `
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Инв. №</th>
                        <th>Заглавие</th>
                        <th>Автор</th>
                        <th>Жанр</th>
                        <th>Година</th>
                        <th>Наличност</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>${tableBodyHtml}</tbody>
            </table>`;
    }

    function renderPagination(pagination) {
        if (!paginationContainer) return;
        
        const currentPage = pagination.page;
        const totalPages = pagination.total_pages;

        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHtml = '<nav><ul class="pagination justify-content-center">';
        paginationHtml += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage - 1}">Предишна</a></li>`;

        const pagesToShow = new Set([1]);
        const windowSize = 2;
        for (let i = Math.max(2, currentPage - windowSize); i <= Math.min(totalPages - 1, currentPage + windowSize); i++) {
            pagesToShow.add(i);
        }
        if (totalPages > 1) pagesToShow.add(totalPages);

        let lastPage = 0;
        for (const page of Array.from(pagesToShow).sort((a, b) => a - b)) {
            if (lastPage !== 0 && page > lastPage + 1) {
                paginationHtml += '<li class="page-item disabled"><span class="page-link">…</span></li>';
            }
            paginationHtml += `<li class="page-item ${page === currentPage ? 'active' : ''}"><a class="page-link" href="#" data-page="${page}">${page}</a></li>`;
            lastPage = page;
        }

        paginationHtml += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage + 1}">Следваща</a></li>`;
        paginationHtml += '</ul></nav>';
        paginationContainer.innerHTML = paginationHtml;
    }

    function updateTotalBooksCount(total) {
        if (totalBooksCount) totalBooksCount.textContent = total;
    }

    // --- Общи функции и Event Listeners ---
    function populateGenreDatalists(genres) {
        const datalistAdd = document.getElementById('genreDatalist_add');
        const datalistEdit = document.getElementById('genreDatalist_edit');
        
        const optionsHtml = genres.map(genre => `<option value="${genre.name}">`).join('');

        if (datalistAdd) {
            datalistAdd.innerHTML = optionsHtml;
        }
        if (datalistEdit) {
            datalistEdit.innerHTML = optionsHtml;
        }
    }

    // Добавяме event listeners само ако елементите съществуват
    if (searchInput && searchButton) {
        searchInput.addEventListener('keyup', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                fetchBooks(1, searchInput.value);
            }, 300);
        });

        searchButton.addEventListener('click', () => {
            clearTimeout(debounceTimer);
            fetchBooks(1, searchInput.value);
        });
    }

    if (paginationContainer) {
        paginationContainer.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && e.target.dataset.page) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page, 10);
                if (page !== currentPage) {
                    fetchBooks(page, currentQuery);
                }
            }
        });
    }
    
    // Този listener ще работи и на двете страници
    document.body.addEventListener('click', async (e) => {
        const editButton = e.target.closest('.edit-book-btn');
        if (!editButton) return;

        const bookId = editButton.dataset.bookId;
        const form = document.getElementById('editBookForm');
        const coverPreview = document.getElementById('coverPreview_edit');
        
        form.reset();
        coverPreview.style.display = 'none';
        coverPreview.src = '';
        document.getElementById('current_cover').value = '';

        try {
            // **КОРЕКЦИЯ**: Първо се уверяваме, че имаме списък с жанрове
            if (allGenres.length === 0) {
                const genresResponse = await fetch('/api/books');
                if (genresResponse.ok) {
                    const listData = await genresResponse.json();
                    allGenres = listData.genres;
                    populateGenreDatalists(allGenres);
                }
            }

            // След това зареждаме данните за конкретната книга
            const bookResponse = await fetch(`/api/book/${bookId}`);
            if (!bookResponse.ok) throw new Error('Could not fetch book data.');
            const book = await bookResponse.json();

            // Попълваме всички полета
            document.getElementById('edit_inv_number').value = book.tom_no || '';
            document.getElementById('edit_title').value = book.title || '';
            document.getElementById('edit_author').value = book.author || '';
            document.getElementById('edit_isbn').value = book.isbn || '';
            document.getElementById('edit_genre').value = book.genre || '';
            document.getElementById('edit_publish_year').value = book.publish_year || '';
            document.getElementById('edit_price').value = book.price || '';
            document.getElementById('edit_is_donation').checked = book.is_donation;
            document.getElementById('current_cover').value = book.cover_image || '';

            if (book.cover_image) {
                coverPreview.src = `/covers/${book.cover_image}`;
                coverPreview.style.display = 'block';
            }
            
            form.action = `/edit_book/${bookId}`;

        } catch (error) {
            console.error("Error fetching book for edit:", error);
        }
    });

    // Първоначално зареждане - ще се случи само ако сме на страницата със списъка
    if (tableContainer) {
        const urlParams = new URLSearchParams(window.location.search);
        const pageFromUrl = parseInt(urlParams.get('page')) || 1;
        const queryFromUrl = urlParams.get('query') || '';
        if (queryFromUrl) {
            searchInput.value = queryFromUrl;
        }
        fetchBooks(pageFromUrl, queryFromUrl);
    }
});