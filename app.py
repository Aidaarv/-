from flask import Flask, render_template, request, redirect, session
import database

app = Flask(__name__)
app.secret_key = 'super_secret_books_key'
database.init_db()

@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', '').strip()
    
    books = database.get_all_books(search_query, sort_by)
    stats = database.get_statistics()
    
    return render_template(
        'index.html',
        books=books,
        stats=stats,
        logged_in=session.get('logged_in', False),
        username=session.get('username')
    )

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    year = request.form.get('year', '').strip()
    genre = request.form.get('genre', '').strip()
    status = request.form.get('status', 'Хочу прочитать')
    rating = request.form.get('rating')
    notes = request.form.get('notes', '').strip()
    
    if title and author:
        # Превращаем рейтинг в число или в None, если книга еще не прочитана
        rating = int(rating) if rating and status == 'Прочитано' else None
        year = int(year) if year else None
        
        database.add_book(title, author, year, genre, status, rating, notes)
        session['success'] = True
        
    return redirect('/')

@app.route('/status/<int:book_id>/<string:new_status>')
def change_status(book_id, new_status):
    if new_status in ['Читаю', 'Прочитано', 'Хочу прочитать']:
        database.update_book_status(book_id, new_status)
    return redirect('/')

@app.route('/delete/<int:book_id>')
def delete(book_id):
    # Удаление доступно только админу
    if session.get('logged_in'):
        database.delete_book(book_id)
    return redirect('/')

@app.route('/detail/<int:book_id>')
def detail(book_id):
    book = database.get_book_by_id(book_id)
    if not book:
        return "Книга не найдена", 404
    return render_template('detail.html', book=book)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if database.check_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect('/')
        else:
            error = 'Неверный логин или пароль'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)