CREATE TABLE IF NOT EXISTS genres ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE NOT NULL );
CREATE TABLE IF NOT EXISTS professions ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE NOT NULL );
CREATE TABLE IF NOT EXISTS educations ( id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(255) UNIQUE NOT NULL );
CREATE TABLE IF NOT EXISTS books ( tom_no VARCHAR(255) PRIMARY KEY, isbn VARCHAR(255), author VARCHAR(255) NOT NULL, title VARCHAR(255) NOT NULL, genre VARCHAR(255), publish_year INT, record_date DATE, price DECIMAL(10, 2), is_donation BOOLEAN DEFAULT FALSE, cover_image TEXT );

CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5( tom_no, title, author, content='books', content_rowid='tom_no', tokenize = "unicode61 remove_diacritics 2" );
CREATE TRIGGER IF NOT EXISTS books_after_insert AFTER INSERT ON books BEGIN INSERT INTO books_fts(rowid, tom_no, title, author) VALUES (new.tom_no, new.tom_no, new.title, new.author); END;
CREATE TRIGGER IF NOT EXISTS books_after_delete AFTER DELETE ON books BEGIN INSERT INTO books_fts(books_fts, rowid, tom_no, title, author) VALUES('delete', old.tom_no, old.tom_no, old.title, old.author); END;
CREATE TRIGGER IF NOT EXISTS books_after_update AFTER UPDATE ON books BEGIN INSERT INTO books_fts(books_fts, rowid, tom_no, title, author) VALUES('delete', old.tom_no, old.tom_no, old.title, old.author); INSERT INTO books_fts(rowid, tom_no, title, author) VALUES (new.tom_no, new.tom_no, new.title, new.author); END;

CREATE TABLE IF NOT EXISTS readers ( reader_no VARCHAR(255) PRIMARY KEY, full_name VARCHAR(255) NOT NULL, city VARCHAR(255), address TEXT, phone VARCHAR(50), email VARCHAR(255), profession VARCHAR(255), education VARCHAR(255), gender VARCHAR(10), registration_date DATE, is_under_14 BOOLEAN DEFAULT FALSE, last_registration_year INT );

-- ПРОМЯНА: borrow_date и return_date вече са DATETIME
CREATE TABLE IF NOT EXISTS borrows (
    borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_tom_no VARCHAR(255) NOT NULL,
    reader_no VARCHAR(255) NOT NULL,
    borrow_date DATETIME NOT NULL,
    due_date DATE NOT NULL,
    return_date DATETIME,
    signature_path TEXT,
    fine_amount REAL DEFAULT 0,
    fine_paid_date DATE,
    FOREIGN KEY (book_tom_no) REFERENCES books(tom_no),
    FOREIGN KEY (reader_no) REFERENCES readers(reader_no)
);

-- ПРОМЯНА: Добавени полета за сигурност при вход
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'librarian',
    failed_login_attempts INTEGER DEFAULT 0,
    lockout_until DATETIME
);
CREATE TABLE IF NOT EXISTS activity_log ( id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, username TEXT NOT NULL, action TEXT NOT NULL, details TEXT );

-- НОВА ТАБЛИЦА ЗА НАСТРОЙКИ
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

-- ДОБАВЯНЕ НА НАЧАЛНИ СТОЙНОСТИ ЗА НАСТРОЙКИТЕ
INSERT OR IGNORE INTO settings (key, value, description) VALUES
('borrow_period', '20', 'Срок за заемане на книга (в дни)'),
('fine_per_day', '0.10', 'Глоба за просрочие на ден (в лв.)'),
('books_per_page', '10', 'Брой книги, показвани на страница');