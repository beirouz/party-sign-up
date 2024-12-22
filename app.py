import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# user data (username, password)
users = {"forouz": "pass!@", 
         "marzieh": "pass!",
         "elahe": "pass!",
         "vida": "pass!",
         "zahra": "pass!",
         "bahar": "pass!",
         "ela": "pass!",
         "elmira": "pass!",
         "kiana": "pass!",
         "sanaz": "pass!"}

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
        # Check if the login is successful
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))  # Redirect to Home after successful login
        else:
            return render_template('home.html', error="Invalid login credentials.")
    
    # Display the home page (if logged in, show event details)
    if 'logged_in' in session and session['logged_in']:
        return render_template('home.html', logged_in=True, username=session['username'], event=event_details)

    # If not logged in, just show the login form
    return render_template('home.html', logged_in=False)


SONGS_FILE = 'songs.json'

def load_songs():
    """Load songs from songs.json."""
    try:
        with open(SONGS_FILE, 'r') as file:
            return sorted(json.load(file), key=lambda x: x['username'].lower())
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_songs(songs):
    """Save songs to songs.json sorted by username alphabetically."""
    with open(SONGS_FILE, 'w') as file:
        json.dump(sorted(songs, key=lambda x: x['username'].lower()), file, indent=4)

@app.route('/karaoke', methods=['GET', 'POST'])
def karaoke():
    if 'logged_in' in session and session['logged_in']:
        songs = load_songs()
        username = session['username']

        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'add':
                # Add a new song
                song = request.form.get('song', '').strip()
                youtube_link = request.form.get('youtube_link', '').strip()

                if not song:
                    return render_template('karaoke.html', songs=songs, error="Song name cannot be empty.")
                
                # Add the song with YouTube link
                songs.append({
                    'username': username,
                    'song': song,
                    'youtube_link': youtube_link
                })
                save_songs(songs)
                return redirect(url_for('karaoke'))

            elif action == 'remove':
                # Remove an existing song
                song = request.form.get('song', '').strip()
                songs = [entry for entry in songs if not (entry['username'] == username and entry['song'] == song)]
                save_songs(songs)
                return redirect(url_for('karaoke'))

        return render_template('karaoke.html', songs=songs)

    return redirect(url_for('home'))

# Route for expenses - Expenses
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'logged_in' in session and session['logged_in']:
        # Load existing data
        table_data = load_expenses()
        username = session['username']
        users = list(table_data.keys())  # List of all users in the table

        if request.method == 'POST':
            # Handle adding a new expense
            if "add_expense" in request.form:
                item_name = request.form.get("item_name")
                amount = float(request.form.get("amount", 0))
                selected_users = request.form.getlist("selected_users")

                if not item_name or amount <= 0:
                    flash("Please provide a valid item name and amount.", "error")
                elif not selected_users:
                    flash("Please select at least one user.", "error")
                else:
                    # Calculate expense distribution
                    n = len(selected_users)
                    x = round(-1 * amount / n, 2)
                    if username in selected_users:
                        y = round(amount + x, 2)
                    else:
                        y = round(amount, 2)
                        

                    # Add new column and update totals
                    new_column_name = f"{item_name}-{username}"
                    for user in selected_users:
                        table_data[user][new_column_name] = x
                    table_data[username][new_column_name] = y

                    # Update totals
                    for user in users:
                        table_data[user]["Total"] = round(sum(
                            value for key, value in table_data[user].items() if key != "Total"
                        ), 2)

                    # Save the updated data
                    save_expenses(table_data)
                    flash("Expense added successfully!", "success")

            elif "remove_expense" in request.form:
                # Handle removing an expense
                column_to_remove = request.form.get("expense_to_remove")

                if not column_to_remove:
                    flash("Please select an expense column to remove.", "error")
                elif not column_to_remove.endswith(f"-{username}"):
                    # Verify if the user is allowed to remove the column
                    flash("You are not allowed to remove other users' expenses.", "error")
                else:
                    # Remove the selected column from each user's data
                    for user in users:
                        if column_to_remove in table_data[user]:
                            del table_data[user][column_to_remove]

                    # Recalculate totals for all users
                    for user in users:
                        table_data[user]["Total"] = round(sum(
                            value for key, value in table_data[user].items() if key != "Total"
                        ), 2)

                    save_expenses(table_data)
                    flash("Expense removed successfully!", "success")

        # Extract all unique columns across the data
        all_columns = set()
        for user_data in table_data.values():
            all_columns.update(user_data.keys())
        all_columns = list(all_columns)  # Ensure columns are iterable
        if "Total" in all_columns:
            all_columns.remove("Total")
            all_columns.append("Total")

        # Pass the extracted columns and table data to the template
        return render_template('expenses.html', table_data=table_data, columns=all_columns, users=users)

    return redirect(url_for('home'))  # Redirect to login if not logged in


def load_expenses():
    """Load expense data from the JSON file."""
    try:
        with open('expenses.json', "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize default structure if the file doesn't exist or is invalid
        return {user: {"Total": 0} for user in users.keys()}

def save_expenses(data):
    """Save expenses to a JSON file."""
    with open('expenses.json', 'w') as file:
        json.dump(data, file, indent=4)

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)