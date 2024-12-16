import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# user data (username, password)
users = {"user1": "pass!", 
         "user2": "pass@",
         "user3": "pass#",
         "user4": "pass$",
         "user5": "pass%",
         "user6": "pass^",
         "user7": "pass&",
         "user8": "pass*",
         "user9": "pass(",
         "user10": "pass)",
         "user11": "pass+"}

# event details
event_details = {
    'address': '123 Party St, Partyville',
    'agenda': 'Food, Drinks, Games, Dancing',
    'timing': '7:00 PM - 11:00 PM'
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
        crust_types = ['Thin Crust', 'Thick Crust', 'Gluten-Free Crust']
        sauces = ['Tomato Sauce', 'Barbecue Sauce', 'Pesto Sauce']
        topping_options = ['Cheese', 'Pepperoni', 'Mushrooms', 'Onions', 'Olives', 'Bacon', 'Peppers']

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

#Route for Appetizer
@app.route('/appetizer', methods=['GET', 'POST'])
def appetizer():
    if 'logged_in' in session and session['logged_in']:
        # Load existing appetizers
        appetizers = load_appetizers()

        if request.method == 'POST':
            # Get the appetizer from the form
            appetizer = request.form['appetizer'].strip()

            if not appetizer:
                return render_template(
                    'appetizer.html',
                    error="You must enter an appetizer.",
                    appetizers=appetizers
                )

            # Check if the user already has an appetizer
            user_appetizer = next(
                (entry for entry in appetizers if entry['username'] == session['username']), None
            )

            if user_appetizer:
                # Update the user's existing appetizer
                user_appetizer['appetizer'] = appetizer
            else:
                # Add a new appetizer entry for the user
                entry = {'username': session['username'], 'appetizer': appetizer}
                appetizers.append(entry)

            # Save updated appetizers
            save_appetizers(appetizers)

            # Redirect back to avoid resubmission issues
            return redirect(url_for('appetizer'))

        return render_template('appetizer.html', appetizers=appetizers)

    return redirect(url_for('home'))  # Redirect to login if not logged in


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