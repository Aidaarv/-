import os
import sys
import pytest

# Подгружаем корневую директорию проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    database.DATABASE = 'test_books.db'
    database.init_db()
    
    with app.test_client() as client:
        yield client
        
    try:
        conn = database.get_db_connection()
        conn.execute('DROP TABLE IF EXISTS books')
        conn.execute('DROP TABLE IF EXISTS users')
        conn.commit()
        conn.close()
    except Exception:
        pass

def test_main_page_loading(client):
    """Проверяем, загружается ли главная страница"""
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Книжный трекер' in html or 'Список книг' in html

def test_add_book_to_tracker(client):
    """Проверяем успешное добавление книги"""
    response = client.post('/add', data={
        'title': 'Преступление и наказание',
        'author': 'Фёдор Достоевский',
        'year': '1866',
        'genre': 'Классика',
        'status': 'Прочитано',
        'rating': '5',
        'notes': 'Очень глубокая вещь.'
    }, follow_redirects=True)
    
    html = response.get_data(as_text=True)
    assert 'Преступление и наказание' in html
    
    # Проверка внутри базы
    conn = database.get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE title = 'Преступление и наказание'").fetchone()
    conn.close()
    assert book is not None
    assert book['author'] == 'Фёдор Достоевский'
    assert book['rating'] == 5

def test_book_search_filtering(client):
    """Проверка работы поиска"""
    database.add_book('Хоббит', 'Джон Толкин', 1937, 'Фэнтези', 'Хочу прочитать', None, '')
    database.add_book('Мастер и Маргарита', 'Михаил Булгаков', 1967, 'Роман', 'Читаю', None, '')
    
    response = client.get('/?q=Хоббит')
    html = response.get_data(as_text=True)
    assert 'Хоббит' in html
    assert 'Мастер и Маргарита' not in html

def test_invalid_book_id_returns_404(client):
    """Проверка обработки ошибки 404 для несуществующей книги"""
    response = client.get('/detail/9999')
    assert response.status_code == 404

def test_statistics_calculation(client):
    """Проверка верного подсчета статистики в БД"""
    database.add_book('Книга 1', 'Автор 1', 2020, 'Наука', 'Прочитано', 5, '')
    database.add_book('Книга 2', 'Автор 2', 2021, 'Наука', 'Прочитано', 3, '')
    
    stats = database.get_statistics()
    assert stats['read'] == 2
    assert stats['avg_rating'] == 4.0