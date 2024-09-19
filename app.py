from flask import Flask, render_template, request, redirect, url_for, session
import os
import random
import uuid  # Import uuid for unique identifiers


app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'  # Replace with a secure key in production

# Predefined list of 20 books with emojis
BOOK_LIST = [
    "📖 The Great Adventure",
    "🔍 Mystery of the Lost Treasure",
    "🚀 Journey to the Moon",
    "🌴 Secrets of the Jungle",
    "🏴‍☠️ Pirates of the Silver Sea",
    "🌲 The Enchanted Forest",
    "🪐 Space Explorers",
    "🏰 The Hidden Kingdom",
    "📜 Legends of the Ancient",
    "⏳ Time Travelers",
    "✨ The Magical Realm",
    "🐠 Underwater Wonders",
    "🐉 Dragon's Quest",
    "☁️ Castle in the Clouds",
    "🛡️ The Brave Knight",
    "🤖 Robot Revolution",
    "🌷 The Secret Garden",
    "👽 Alien Encounters",
    "👻 The Haunted House",
    "🦸 Superhero Saga"
]

# Initialize game state
def init_game():
    session['dollars'] = 3
    session['inventory'] = []
    session['day'] = 1
    session['messages'] = []
    session['available_books'] = BOOK_LIST.copy()
    session.modified = True  # Ensure session updates are saved

# Simulate customer behavior
def customer_visit(shop):
    purchased = []
    for book in shop:
        # Define purchasing probability based on sell_price
        if book['sell_price'] <= 2:
            chance = 0.5  # 50% chance to buy
        elif book['sell_price'] <= 4:
            chance = 0.3  # 30% chance to buy
        else:
            chance = 0.1  # 10% chance to buy
        
        if random.random() < chance:
            purchased.append(book)
    return purchased

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_name' not in session:
        # Handle user name input
        if request.method == 'POST' and request.form.get('action') == 'set_name':
            user_name = request.form.get('user_name').strip()
            if user_name:
                session['user_name'] = user_name
                init_game()
                session['messages'].append(f"👋 Welcome, {user_name}! Welcome to {user_name}'s Bookstore.")
                return redirect(url_for('index'))
            else:
                # Handle empty name submission
                modal_data = {
                    'title': '⚠️ Name Required',
                    'body': "Please enter your name to start the game."
                }
                return render_template('index.html',
                                       dollars=0,
                                       inventory=[],
                                       day=1,
                                       messages=[],
                                       book_list=BOOK_LIST,
                                       modal_data=modal_data,
                                       user_name='')
        else:
            # Show the name input modal
            modal_data = {
                'title': "👤 What Is Your Name?",
                'body': '''
                    <form method="POST">
                        <input type="hidden" name="action" value="set_name">
                        <div class="mb-3">
                            <label for="user_name" class="form-label">Please enter your name:</label>
                            <input type="text" id="user_name" name="user_name" class="form-control large-input" required>
                        </div>
                        <button type="submit" class="btn btn-primary">👍 Submit</button>
                    </form>
                '''
            }
            return render_template('index.html',
                                   dollars=0,
                                   inventory=[],
                                   day=1,
                                   messages=[],
                                   book_list=BOOK_LIST,
                                   modal_data=modal_data,
                                   user_name='')
    
    if 'dollars' not in session:
        init_game()

    modal_data = None  # Data to pass to modal

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'buy_books':
            try:
                quantity = int(request.form.get('quantity', 0))
                buy_price = int(request.form.get('buy_price', 1))
                selected_book = request.form.get('selected_book')
            except (ValueError, TypeError):
                quantity = 0
                buy_price = 1
                selected_book = None

            total_cost = quantity * buy_price

            if (selected_book in session['available_books'] and
                buy_price in [1, 2] and
                quantity > 0 and
                session['dollars'] >= total_cost):

                session['dollars'] -= total_cost
                bought_books = []
                for _ in range(quantity):
                    # Assign the selected book with a unique ID
                    book_title = selected_book
                    session['inventory'].append({
                        'id': str(uuid.uuid4()),  # Unique identifier
                        'title': book_title,
                        'buy_price': buy_price,
                        'sell_price': 1  # Default sell price
                    })
                    bought_books.append(book_title)
                session['messages'].append(f"🛒 Bought {quantity} book(s): {', '.join(bought_books)} for 💰 ${total_cost}.")
                session.modified = True  # Ensure session updates are saved

                # Debug: Print inventory after purchase
                print("Inventory after purchase:", session['inventory'])

                # Prepare modal data
                modal_data = {
                    'title': '📦 Purchase Successful!',
                    'body': f"You bought {quantity} book(s): {', '.join(bought_books)}<br>Spent: 💰 ${total_cost}<br>Dollars on Hand: 💵 ${session['dollars']}"
                }
            else:
                session['messages'].append("❌ Not enough Dollars, invalid price, or book unavailable.")
                session.modified = True  # Ensure session updates are saved
                modal_data = {
                    'title': '⚠️ Purchase Failed!',
                    'body': "Not enough Dollars, invalid price, or book unavailable."
                }

        elif action == 'set_prices':
            sell_prices = request.form.getlist('sell_price')
            book_ids = request.form.getlist('book_id')
            updated_books = []

            for book_id, price in zip(book_ids, sell_prices):
                try:
                    price = int(price)
                    if price < 1:
                        price = 1
                    # Find the book in inventory by ID and update its sell_price
                    for book in session['inventory']:
                        if book['id'] == book_id:
                            book['sell_price'] = price
                            updated_books.append(f"{book['title']} ➡️ ${price}")
                            break
                except ValueError:
                    continue

            if updated_books:
                session['messages'].append("✏️ Set sell prices for your books.")
                modal_data = {
                    'title': '💵 Prices Updated!',
                    'body': "You have set the following sell prices:<br>" + "<br>".join(updated_books) + f"<br>Dollars on Hand: 💵 ${session['dollars']}"
                }
            else:
                session['messages'].append("⚠️ No valid prices were updated.")
                modal_data = {
                    'title': '⚠️ Update Failed!',
                    'body': "No valid sell prices were set."
                }
            session.modified = True  # Ensure session updates are saved

            # Debug: Print inventory after setting prices
            print("Inventory after setting prices:", session['inventory'])

        elif action == 'open_shop':
            # Customer visits
            purchased = customer_visit(session['inventory'])
            total_revenue = sum(book['sell_price'] for book in purchased)
            session['dollars'] += total_revenue
            session['messages'].append(f"👥 Customer bought {len(purchased)} book(s) for 💰 ${total_revenue}.")
            session.modified = True  # Ensure session updates are saved

            # Remove purchased books from inventory and add back to available_books
            returned_books = []
            for book in purchased:
                if book in session['inventory']:
                    session['inventory'].remove(book)
                    session['available_books'].append(book['title'])
                    returned_books.append(book['title'])

            # Increment day
            session['day'] += 1
            session['messages'].append(f"📅 Day {session['day']} begins.")
            session.modified = True  # Ensure session updates are saved

            # Prepare modal data
            if purchased:
                modal_data = {
                    'title': '🛍️ Customer Visit!',
                    'body': f"Customer bought {len(purchased)} book(s): {', '.join(returned_books)}<br>Earned: 💰 ${total_revenue}<br>Dollars on Hand: 💵 ${session['dollars']}"
                }
            else:
                modal_data = {
                    'title': '😞 No Sales Today',
                    'body': f"No books were purchased today.<br>Dollars on Hand: 💵 ${session['dollars']}"
                }

            # Debug: Print inventory after customer visit
            print("Inventory after customer visit:", session['inventory'])

    return render_template('index.html',
                           dollars=session.get('dollars', 0),
                           inventory=session.get('inventory', []),
                           day=session.get('day', 1),
                           messages=session.get('messages', []),
                           book_list=BOOK_LIST,
                           modal_data=modal_data,
                           user_name=session.get('user_name', ''))

@app.route('/reset')
def reset():
    init_game()
    session.pop('user_name', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
