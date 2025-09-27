// static/dashboard_logic.js (Финална версия)

document.addEventListener('DOMContentLoaded', function() {
    
    // --- Елементи за Модален Прозорец "Книга" ---
    const bookModal = document.getElementById('addBookModal');
    const openBookModalBtn = document.getElementById('openAddBookModal');
    const addBookForm = document.getElementById('addBookForm');

    // --- Елементи за Модален Прозорец "Читател" ---
    const readerModal = document.getElementById('addReaderModal');
    const openReaderModalBtn = document.getElementById('openAddReaderModal');
    const addReaderForm = document.getElementById('addReaderForm');

    // --- Функция за отваряне на прозорец "Книга" ---
    if (openBookModalBtn && bookModal) {
        openBookModalBtn.onclick = function() {
            bookModal.style.display = "block";
        }
    }

    // --- Функция за отваряне на прозорец "Читател" ---
    if (openReaderModalBtn && readerModal) {
        openReaderModalBtn.onclick = function() {
            readerModal.style.display = "block";
        }
    }
    
    // --- Функции за затваряне на прозорците с хикс (X) ---
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(btn => {
        btn.onclick = function() {
            if (bookModal) bookModal.style.display = "none";
            if (readerModal) readerModal.style.display = "none";
        }
    });

    // --- Логика за Формата за Книги ---
    if (addBookForm) {
        addBookForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const genreSelect = addBookForm.querySelector('#genre-select');
            const newGenreInput = addBookForm.querySelector('#new-genre-input');
            let finalGenre = (genreSelect.value === 'add_new') ? newGenreInput.value : genreSelect.value;
            if (genreSelect.value === 'add_new' && !finalGenre) { alert('Моля, въведете име за новия жанр.'); return; }

            const bookData = {
                inv_number: addBookForm.querySelector('#inv-number').value,
                title: addBookForm.querySelector('#title').value,
                author: addBookForm.querySelector('#author').value,
                isbn: addBookForm.querySelector('#isbn').value,
                genre: finalGenre,
                publish_year: addBookForm.querySelector('#publish-year').value,
                price: addBookForm.querySelector('#price').value,
                is_donation: addBookForm.querySelector('#is-donation').checked
            };

            fetch('/add_book', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(bookData) })
            .then(response => response.json())
            .then(data => {
                alert(data.message); 
                if (data.status === 'success') {
                    // КОРЕКЦИЯТА Е ТУК: Само изчистваме формата
                    addBookForm.reset();
                    newGenreInput.style.display = 'none';
                }
            })
            .catch(error => console.error('Грешка:', error));
        });

        const genreSelect = addBookForm.querySelector('#genre-select');
        const newGenreInput = addBookForm.querySelector('#new-genre-input');
        genreSelect.addEventListener('change', function() {
            newGenreInput.style.display = (this.value === 'add_new') ? 'block' : 'none';
        });
    }

    // --- Логика за Формата за Читатели ---
    if (addReaderForm) {
        const professionSelect = addReaderForm.querySelector('#profession-select');
        const newProfessionInput = addReaderForm.querySelector('#new-profession-input');
        const educationSelect = addReaderForm.querySelector('#education-select');
        const newEducationInput = addReaderForm.querySelector('#new-education-input');

        professionSelect.addEventListener('change', function() { newProfessionInput.style.display = (this.value === 'add_new') ? 'block' : 'none'; });
        educationSelect.addEventListener('change', function() { newEducationInput.style.display = (this.value === 'add_new') ? 'block' : 'none'; });

        addReaderForm.addEventListener('submit', function(event) {
            event.preventDefault();
            let finalProfession = (professionSelect.value === 'add_new') ? newProfessionInput.value : professionSelect.value;
            if (professionSelect.value === 'add_new' && !finalProfession) { alert('Моля, въведете нова професия.'); return; }
            let finalEducation = (educationSelect.value === 'add_new') ? newEducationInput.value : educationSelect.value;
            if (educationSelect.value === 'add_new' && !finalEducation) { alert('Моля, въведете ново образование.'); return; }

            const readerData = {
                reader_no: addReaderForm.querySelector('#reader-number').value,
                full_name: addReaderForm.querySelector('#full-name').value,
                city: addReaderForm.querySelector('#city').value,
                address: addReaderForm.querySelector('#address').value,
                phone: addReaderForm.querySelector('#phone').value,
                email: addReaderForm.querySelector('#email').value,
                profession: finalProfession,
                education: finalEducation,
                gender: addReaderForm.querySelector('#gender-select').value,
                is_under_14: addReaderForm.querySelector('#under-14').checked
            };
            
            fetch('/add_reader', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(readerData) })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.status === 'success') {
                    // КОРЕКЦИЯТА Е ТУК: Само изчистваме формата
                    addReaderForm.reset();
                    newProfessionInput.style.display = 'none';
                    newEducationInput.style.display = 'none';
                }
            })
            .catch(error => console.error('Грешка:', error));
        });
    }
});