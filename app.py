import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname='party_e6wy',
        user='party_e6wy_user',
        password='BRN94u0xDPccMAe2vacvK8mMM3PLAGeJ',
        host='dpg-ctk821bqf0us739g4ubg-a.oregon-postgres.render.com',
        port='5432'
    )
# event details
event_details = {
    'address': 'Radiance Party Room, 23 Sheppard Avenue East, North York, ON',
    'agenda': 'Food, Drinks, Games, Dancing',
    'timing': 'TBD (Most likely 5:00 pm)'
}

# Route for the Home page (login page and post-login view)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('home.html', error="Invalid login credentials.")

    if 'logged_in' in session and session['logged_in']:
        return render_template('home.html', logged_in=True, username=session['username'], event=event_details)

    return render_template('home.html', logged_in=False)

# Karaoke Route
@app.route('/karaoke', methods=['GET', 'POST'])
def karaoke():
    if 'logged_in' in session and session['logged_in']:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        username = session['username']
        cur.execute("SELECT username, song, youtube_link FROM user_songs ORDER BY username")
        songs = cur.fetchall()

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add':
                song = request.form.get('song', '').strip()
                youtube_link = request.form.get('youtube_link', '').strip()
                if not song:
                    cur.close()
                    conn.close()
                    return render_template('karaoke.html', songs=songs, error="Song name cannot be empty.")

                cur.execute("INSERT INTO user_songs (username, song, youtube_link) VALUES (%s, %s, %s)",
                            (username, song, youtube_link))
                conn.commit()

            elif action == 'remove':
                song = request.form.get('song', '').strip()
                cur.execute("DELETE FROM user_songs WHERE username = %s AND song = %s", (username, song))
                conn.commit()

            cur.execute("SELECT username, song, youtube_link FROM user_songs ORDER BY username")
            songs = cur.fetchall()

        cur.close()
        conn.close()
        return render_template('karaoke.html', songs=songs)

    return redirect(url_for('home'))

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'logged_in' in session and session['logged_in']:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        username = session['username']
        cur.execute("SELECT * FROM user_expenses ORDER BY username")
        expenses = cur.fetchall()

        # Fetch list of all users
        cur.execute("SELECT username FROM users")
        users = [user['username'] for user in cur.fetchall()]

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add_expense':
                item_name = request.form.get("item_name")
                amount = float(request.form.get("amount", 0))
                selected_users = request.form.getlist("selected_users")

                # List of all usernames in the database
                cur.execute("SELECT username FROM users")
                all_users = [user['username'] for user in cur.fetchall()]

                if not item_name or amount <= 0:
                    flash("Please provide a valid item name and amount.", "error")
                elif not selected_users:
                    flash("Please select at least one user.", "error")
                else:
                    # Calculate the expense distribution
                    n = len(selected_users)
                    per_user_share = round(-1 * amount / n, 2)
                    if username in selected_users:
                        payer_share = round(amount + per_user_share, 2)
                    else:
                        payer_share = round(amount, 2)

                    # Initialize expense data for all users
                    expense_data = {user: 0 for user in all_users}

                    # Update payer's amount
                    expense_data[username] = payer_share

                    # Update selected users' amounts
                    for user in selected_users:
                        if user != username:
                            expense_data[user] = per_user_share

                    # Prepare data for the query
                    values = [username, item_name, amount] + [expense_data[user] for user in all_users]

                    # Insert query
                    query = f"""
                    INSERT INTO user_expenses (
                        username, item, amount, {', '.join(all_users)}
                    ) VALUES (%s, %s, %s, {', '.join(['%s'] * len(all_users))})
                    """
                    try:
                        cur.execute(query, values)
                        conn.commit()
                        flash("Expense added successfully.", "success")
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error: {e}", "error")

            elif action == 'remove_expense':
                item_name = request.form.get("item_name")
                cur.execute(
                    "DELETE FROM user_expenses WHERE username = %s AND item = %s",
                    (username, item_name),
                )
                conn.commit()

            # Fetch updated expenses
            cur.execute("SELECT * FROM user_expenses ORDER BY username")
            expenses = cur.fetchall()

        cur.close()
        conn.close()
        return render_template('expenses.html', table_data=expenses, users=users)

    return redirect(url_for('home'))


# Route for logging out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
