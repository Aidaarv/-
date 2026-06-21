import sqlite3

DATABASE = 'books_tracker.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Таблица книг
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            genre TEXT,
            status TEXT NOT NULL, -- 'Читаю', 'Прочитано', 'Хочу прочитать'
            rating INTEGER,       -- от 1 до 5
            notes TEXT
        )
    ''')
    
    # Таблица пользователей (для админа)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Добавляем стандартного админа (пароль: 123)
    conn.execute(
        'INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
        ('admin', '123')
    )
    
    conn.commit()
    conn.close()

def get_all_books(search_query=None, sort_by=None):
    conn = get_db_connection()
    query = 'SELECT * FROM books'
    params = []
    
    if search_query:
        query += ' WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?'
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
        
    if sort_by == 'rating DESC':
        query += ' ORDER BY rating DESC'
    elif sort_by == 'year DESC':
        query += ' ORDER BY year DESC'
    else:
        query += ' ORDER BY id DESC'
        
    books = conn.execute(query, params).fetchall()
    conn.close()
    return books

def get_book_by_id(book_id):
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    return book

def add_book(title, author, year, genre, status, rating, notes):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO books (title, author, year, genre, status, rating, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, year, genre, status, rating, notes))
    conn.commit()
    conn.close()

def update_book_status(book_id, new_status):
    conn = get_db_connection()
    conn.execute('UPDATE books SET status = ? WHERE id = ?', (new_status, book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

def get_statistics():
    """Считает метрики для панели статистики и графиков"""
    conn = get_db_connection()
    
    # Всего книг по статусам
    total_books = conn.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    read_books = conn.execute("SELECT COUNT(*) FROM books WHERE status = 'Прочитано'").fetchone()[0]
    reading_books = conn.execute("SELECT COUNT(*) FROM books WHERE status = 'Читаю'").fetchone()[0]
    want_books = conn.execute("SELECT COUNT(*) FROM books WHERE status = 'Хочу прочитать'").fetchone()[0]
    
    # Средняя оценка прочитанных книг
    avg_rating_row = conn.execute("SELECT AVG(rating) FROM books WHERE status = 'Прочитано' AND rating IS NOT NULL").fetchone()
    avg_rating = round(avg_rating_row[0], 1) if avg_rating_row[0] else 0
    
    # Топ жанров (берём первые 3 популярных)
    genres_rows = conn.execute('''
        SELECT genre, COUNT(*) as count 
        FROM books 
        WHERE genre IS NOT NULL AND genre != "" 
        GROUP BY genre 
        ORDER BY count DESC 
        LIMIT 3
    ''').fetchall()
    
    conn.close()
    
    return {
        'total': total_books,
        'read': read_books,
        'reading': reading_books,
        'want': want_books,
        'avg_rating': avg_rating,
        'top_genres': genres_rows
    }

def check_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return user is not None