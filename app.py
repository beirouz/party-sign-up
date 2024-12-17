import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# user data (username, password)
users = {"forouz": "pass!", 
         "marzieh": "pass!",
         "elahe": "pass!",
         "mina": "pass!",
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

# File to store orders
orders_file = 'orders.json'

def load_orders():
    try:
        with open(orders_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_orders(orders):
    with open(orders_file, 'w') as file:
        json.dump(orders, file, indent=4)

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

@app.route('/dinner', methods=['GET', 'POST'])
def dinner():
    if 'logged_in' in session and session['logged_in']:
        # Define the pizza options
        crust_types = ['Thin Crust', 'Regular Crust', 'Thick Crust']
        sauces = ['Tomato Sauce', 'No Sauce']
        topping_options = ['Fire Roasted Red Peppers', 
                           'Fresh Mushrooms', 
                           'Green Olives', 
                           'Green Peppers', 
                           'Red Onion', 
                           'Roasted Garlic', 
                           'Roma Tomatos',
                           'Sun Dried Tomatos',
                           'Butter Chicken',
                           'Grilled Chicken',
                           'Bacon Strips',
                           'Feta Cheese',
                           'Parmesan Cheese']

        # Load existing orders
        orders = load_orders()

        if request.method == 'POST':
            # Collect the pizza order details from the form
            crust = request.form['crust']
            sauce = request.form['sauce']
            toppings = request.form.getlist('toppings')  # Get all selected toppings as a list

            # Check for valid topping count
            if len(toppings) > 4:
                return render_template('dinner.html', error="You cannot select more than 4 toppings. Please remove extra toppings.", crust_types=crust_types, sauces=sauces, topping_options=topping_options, orders=orders)

            # Check if the user already has an order
            user_order = next((order for order in orders if order['username'] == session['username']), None)

            # If user has an existing order, update it, otherwise add a new one
            if user_order:
                user_order['crust'] = crust
                user_order['sauce'] = sauce
                user_order['toppings'] = toppings
            else:
                # Create a new order if the user does not already have one
                order = {
                    'username': session['username'],
                    'crust': crust,
                    'sauce': sauce,
                    'toppings': toppings
                }
                orders.append(order)

            # Save the updated orders
            save_orders(orders)

            # Redirect back to the dinner page to show the updated order
            return redirect(url_for('dinner'))

        # Render the Dinner page with current orders
        return render_template('dinner.html', crust_types=crust_types, sauces=sauces, topping_options=topping_options, orders=orders)

    return redirect(url_for('home'))  # Redirect to login if not logged in

# Route for Appetizer and Dessert
@app.route('/partypicks', methods=['GET', 'POST'])
def partypicks():
    if 'logged_in' in session and session['logged_in']:
        # Load existing appetizers and desserts
        appetizers = load_appetizers()
        desserts = load_desserts()

        # Initialize lists to display both categories
        appetizer_list = appetizers
        dessert_list = desserts

        selected_category = request.form.get('category', 'Appetizer')

        if request.method == 'POST' and 'item' in request.form:
            # Get the entered item
            item = request.form['item'].strip()

            if not item:
                return render_template(
                    'party-picks.html',
                    error="You must enter a valid item.",
                    selected_category=selected_category,
                    appetizer_list=appetizer_list,
                    dessert_list=dessert_list,
                )

            username = session['username']

            # Remove existing user entry from both lists
            appetizers = [entry for entry in appetizers if entry['username'] != username]
            desserts = [entry for entry in desserts if entry['username'] != username]

            # Add new entry to the selected category
            entry = {'username': username, 'item': item}
            if selected_category == 'Appetizer':
                appetizers.append(entry)
            else:
                desserts.append(entry)

            # Save the updated lists
            save_appetizers(appetizers)
            save_desserts(desserts)

            # Redirect back to avoid resubmission issues
            return redirect(url_for('partypicks'))

        return render_template(
            'party-picks.html',
            selected_category=selected_category,
            appetizer_list=appetizer_list,
            dessert_list=dessert_list,
        )

    return redirect(url_for('home'))  # Redirect to login if not logged in



def load_desserts():
    """Load desserts from dessert.json."""
    try:
        with open('dessert.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return an empty list if the file doesn't exist or is invalid
        return []


def save_desserts(desserts):
    """Save desserts to dessert.json."""
    with open('dessert.json', 'w') as file:
        json.dump(desserts, file, indent=4)


def load_appetizers():
    """Load appetizers from appetizer.json."""
    try:
        with open('appetizer.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return an empty list if the file doesn't exist or is invalid
        return []



def save_appetizers(appetizers):
    """Save appetizers to appetizer.json."""
    with open('appetizer.json', 'w') as file:
        json.dump(appetizers, file, indent=4)


# Route for expenses - Expenses
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'logged_in' in session and session['logged_in']:
        # Load existing data
        table_data = load_expenses()
        username = session['username']
        users = list(table_data.keys())  # List of all users in the table

        if request.method == 'POST':
            # Check which form was submitted
            if "add_expense" in request.form:
                # Handle adding a new expense
                item_name = request.form.get("item_name")
                amount = float(request.form.get("amount", 0))

                if not item_name or amount <= 0:
                    flash("Please provide a valid item name and amount.", "error")
                else:
                    # Calculate X and Y
                    n = len(users)
                    x = round(-1 * amount / n, 2)
                    y = round(amount + x, 2)

                    # Add new column and update totals
                    new_column_name = f"{item_name}-{username}"
                    for user in users:
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

            elif "edit_expense" in request.form:
                # Handle editing an expense
                column_to_edit = request.form.get("column_to_edit")
                updated_amount = float(request.form.get("updated_amount", 0))

                if not column_to_edit or updated_amount <= 0:
                    flash("Please provide a valid column and amount.", "error")
                elif not column_to_edit.endswith(f"-{username}"):
                    # Verify if the user is allowed to edit the column
                    flash("You are not allowed to edit other users' expenses.", "error")
                else:
                    # Calculate new X and Y
                    n = len(users)
                    x = round(-1 * updated_amount / n, 2)
                    y = round(updated_amount + x, 2)

                    # Update the column and totals
                    for user in users:
                        table_data[user][column_to_edit] = x
                    table_data[username][column_to_edit] = y

                    for user in users:
                        table_data[user]["Total"] = round(sum(
                            value for key, value in table_data[user].items() if key != "Total"
                        ), 2)

                    save_expenses(table_data)
                    flash("Expense updated successfully!", "success")
            elif "remove_expense" in request.form:
                # Handle removing an expense
                column_to_remove = request.form.get("column_to_remove")

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
        #all_columns.discard("Total")  # Remove "Total" from being double-rendered as a column header
        all_columns = list(all_columns)  # Ensure columns are iterable
        if "Total" in all_columns:
            all_columns.remove("Total")  # Remove "Total" temporarily
            all_columns.append("Total")  # Add "Total" at the end

        # Pass the extracted columns and table data to the template
        return render_template('expenses.html', table_data=table_data, columns=all_columns)

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