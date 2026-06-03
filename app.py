from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3, os, random

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'flashcards.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#6C63FF',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty INTEGER DEFAULT 0,
            times_seen INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
        )''')
        # Seed sample data
        cur = conn.execute("SELECT COUNT(*) FROM decks")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO decks (name, color) VALUES ('Python Basics', '#6C63FF')")
            conn.execute("INSERT INTO decks (name, color) VALUES ('World Geography', '#FF6584')")
            conn.execute("INSERT INTO decks (name, color) VALUES ('Science Facts', '#43D9AD')")
            sample = [
                (1, 'What does Python stand for?', 'Python is named after Monty Python, not the snake.'),
                (1, 'What is a list in Python?', 'An ordered, mutable collection of items: [1, 2, 3]'),
                (1, 'What is a dictionary?', 'An unordered collection of key-value pairs: {"key": "value"}'),
                (1, 'How do you define a function?', 'Using the def keyword: def my_func():'),
                (2, 'What is the capital of Japan?', 'Tokyo'),
                (2, 'Which is the largest ocean?', 'The Pacific Ocean'),
                (2, 'How many continents are there?', '7 continents: Africa, Antarctica, Asia, Australia, Europe, North America, South America'),
                (3, 'What is the speed of light?', '299,792,458 meters per second (≈ 300,000 km/s)'),
                (3, 'What is H2O?', 'Water — two hydrogen atoms bonded to one oxygen atom'),
                (3, 'What is photosynthesis?', 'The process by which plants use sunlight to convert CO₂ and water into glucose and oxygen'),
            ]
            conn.executemany("INSERT INTO cards (deck_id, question, answer) VALUES (?,?,?)", sample)
        conn.commit()

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    with get_db() as conn:
        decks = conn.execute('''
            SELECT d.*, COUNT(c.id) as card_count,
                   SUM(c.times_correct) as total_correct,
                   SUM(c.times_seen) as total_seen
            FROM decks d LEFT JOIN cards c ON c.deck_id = d.id
            GROUP BY d.id ORDER BY d.created_at DESC
        ''').fetchall()
    return render_template('index.html', decks=decks)

@app.route('/deck/<int:deck_id>')
def deck(deck_id):
    with get_db() as conn:
        d = conn.execute("SELECT * FROM decks WHERE id=?", (deck_id,)).fetchone()
        cards = conn.execute("SELECT * FROM cards WHERE deck_id=? ORDER BY id", (deck_id,)).fetchall()
    if not d:
        return redirect(url_for('index'))
    return render_template('deck.html', deck=d, cards=cards)

@app.route('/quiz/<int:deck_id>')
def quiz(deck_id):
    with get_db() as conn:
        d = conn.execute("SELECT * FROM decks WHERE id=?", (deck_id,)).fetchone()
        cards = conn.execute("SELECT * FROM cards WHERE deck_id=?", (deck_id,)).fetchall()
    if not d or not cards:
        return redirect(url_for('index'))
    return render_template('quiz.html', deck=d, cards=cards)

# ── API ───────────────────────────────────────────────────────────────────────
@app.route('/api/decks', methods=['GET','POST'])
def api_decks():
    with get_db() as conn:
        if request.method == 'POST':
            data = request.json
            cur = conn.execute("INSERT INTO decks (name,color) VALUES (?,?)",
                               (data['name'], data.get('color','#6C63FF')))
            conn.commit()
            return jsonify({'id': cur.lastrowid, 'name': data['name'], 'color': data.get('color','#6C63FF')})
        decks = conn.execute("SELECT d.*, COUNT(c.id) as card_count FROM decks d LEFT JOIN cards c ON c.deck_id=d.id GROUP BY d.id").fetchall()
        return jsonify([dict(r) for r in decks])

@app.route('/api/decks/<int:deck_id>', methods=['PUT','DELETE'])
def api_deck(deck_id):
    with get_db() as conn:
        if request.method == 'DELETE':
            conn.execute("DELETE FROM decks WHERE id=?", (deck_id,))
            conn.commit()
            return jsonify({'success': True})
        data = request.json
        conn.execute("UPDATE decks SET name=?,color=? WHERE id=?",
                     (data['name'], data.get('color','#6C63FF'), deck_id))
        conn.commit()
        return jsonify({'success': True})

@app.route('/api/cards', methods=['GET','POST'])
def api_cards():
    with get_db() as conn:
        if request.method == 'POST':
            data = request.json
            cur = conn.execute("INSERT INTO cards (deck_id,question,answer) VALUES (?,?,?)",
                               (data['deck_id'], data['question'], data['answer']))
            conn.commit()
            return jsonify({'id': cur.lastrowid})
        deck_id = request.args.get('deck_id')
        rows = conn.execute("SELECT * FROM cards WHERE deck_id=?", (deck_id,)).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/cards/<int:card_id>', methods=['PUT','DELETE'])
def api_card(card_id):
    with get_db() as conn:
        if request.method == 'DELETE':
            conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
            conn.commit()
            return jsonify({'success': True})
        data = request.json
        conn.execute("UPDATE cards SET question=?,answer=? WHERE id=?",
                     (data['question'], data['answer'], card_id))
        conn.commit()
        return jsonify({'success': True})

@app.route('/api/cards/<int:card_id>/result', methods=['POST'])
def card_result(card_id):
    data = request.json
    correct = 1 if data.get('correct') else 0
    with get_db() as conn:
        conn.execute("UPDATE cards SET times_seen=times_seen+1, times_correct=times_correct+? WHERE id=?",
                     (correct, card_id))
        conn.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
