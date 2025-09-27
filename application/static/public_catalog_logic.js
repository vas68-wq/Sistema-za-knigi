document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input-public');
    const genreFilter = document.getElementById('genre-filter-public');
    const resultsContainer = document.getElementById('search-results-container');
    const defaultContent = document.getElementById('default-content');
    const loadingSpinner = document.getElementById('loading-spinner-public');
    let debounceTimer;

    function performSearch() {
        const query = searchInput.value;
        const genre = genreFilter.value;

        // Ако няма критерии за търсене, показваме съдържанието по подразбиране
        if (query.length < 2 && !genre) {
            resultsContainer.style.display = 'none';
            defaultContent.style.display = 'block';
            history.replaceState(null, '', '/public_catalog'); // Изчистваме URL
            return;
        }

        loadingSpinner.style.display = 'block';
        // Променяме URL в браузъра, за да запазим състоянието на търсенето
        const newUrl = `/public_catalog?query=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}`;
        history.replaceState(null, '', newUrl);

        fetch(`/api/public_search_books?query=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}`)
            .then(response => response.json())
            .then(data => {
                renderResults(data);
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
                resultsContainer.innerHTML = '<p class="text-danger">Възникна грешка при търсенето.</p>';
            })
            .finally(() => {
                loadingSpinner.style.display = 'none';
            });
    }

    function renderResults(books) {
        defaultContent.style.display = 'none';
        resultsContainer.style.display = 'block';
        resultsContainer.innerHTML = '';

        if (books.length === 0) {
            resultsContainer.innerHTML = '<h4>Резултати от търсенето</h4><p>Няма намерени книги по зададените критерии.</p>';
            return;
        }
        
        // Взимаме текущия URL, който вече е правилният, за да го подадем за "Назад"
        const backUrl = encodeURIComponent(window.location.href);
        let resultsHtml = '<h4 class="mb-3">Резултати от търсенето</h4><div class="row">';

        books.forEach(book => {
            const availabilityClass = book.status === 'Налична' ? 'text-success' : 'text-danger';
            const availabilityText = book.status === 'Налична' ? 'Налична' : `Заета (до ${book.due_date || 'N/A'})`;
            const coverImage = book.cover_image ? `/covers/${book.cover_image}` : '/static/placeholder.png';
            
            // Добавяме back_url към линка за детайли
            const detailUrl = `/book/${book.tom_no}?back_url=${backUrl}`;

            resultsHtml += `
                <div class="col-lg-2 col-md-3 col-sm-4 col-6 mb-4">
                    <div class="card h-100 book-card">
                        <a href="${detailUrl}">
                            <img src="${coverImage}" class="card-img-top" alt="${book.title}">
                        </a>
                        <div class="card-body">
                            <h6 class="card-title">${book.title}</h6>
                            <p class="card-text text-muted">${book.author}</p>
                        </div>
                        <div class="card-footer">
                            <small class="${availabilityClass}">${availabilityText}</small>
                        </div>
                    </div>
                </div>
            `;
        });

        resultsHtml += '</div>';
        resultsContainer.innerHTML = resultsHtml;
    }

    searchInput.addEventListener('keyup', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 300);
    });

    genreFilter.addEventListener('change', performSearch);
    
    // Тази част се изпълнява само ако влезем в страницата с вече зададени параметри за търсене
    const urlParams = new URLSearchParams(window.location.search);
    const queryFromUrl = urlParams.get('query');
    const genreFromUrl = urlParams.get('genre');

    if ((queryFromUrl && queryFromUrl.length >= 2) || (genreFromUrl && genreFromUrl !== '')) {
        searchInput.value = queryFromUrl || '';
        genreFilter.value = genreFromUrl || '';
        performSearch();
    }
});