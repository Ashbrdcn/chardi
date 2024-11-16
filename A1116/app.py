from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages; set to a secure random key in production

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='ecomDB',
            user='root',
            password=''
        )
        if conn.is_connected():
            print("Database connected successfully.")
        return conn
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

# Route to check if the database connection works
@app.route('/check_connection', methods=['GET'])
def check_connection():
    conn = get_db_connection()
    if conn:
        conn.close()  # Close connection after checking
        return jsonify({"message": "Connection successful"})
    else:
        return jsonify({"message": "Connection failed"}), 500

# Login required decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access this page", category="danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Ensure the original function name is preserved
    return wrapper


@app.route('/', methods=['GET'])
def home():
     # Assuming user information is stored in session after login
    user = session.get('user')  # Retrieve user data from session
    is_approved = user.get('is_approved', False) if user else False  # Check if user is approved
    
    return render_template('home.html', is_approved=is_approved)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        if conn is None:
            flash("Database connection error")
            return redirect(url_for('login'))
        
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            # Validate required fields
            if not email or not password:
                flash("Both email and password are required")
                return redirect(url_for('login'))

            cursor = conn.cursor()

            # Fetch the user data
            query = "SELECT id, password, role FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user:
                # Check if the password matches
                if user[1] == password:  # Compare plain text passwords directly
                    session['user_id'] = user[0]  # Store user ID in session
                    session['role'] = user[2]  # Store role in session
                    role = user[2]
                    if role == 'admin':
                        return redirect(url_for('admin_page'))
                    elif role == 'superadmin':
                        return redirect(url_for('super_page'))
                    elif role == 'user':
                        return redirect(url_for('user_page'))
                    else:
                        flash("Unknown role encountered", category="danger")
                        return redirect(url_for('login'))
                else:
                    flash("Invalid email or password", category="danger")
                    return redirect(url_for('login'))
            else:
                flash("Invalid email or password", category="danger")
                return redirect(url_for('login'))

        except Error as e:
            print(f"Login error: {e}")
            flash("An internal database error occurred", category="danger")
            return redirect(url_for('login'))
        finally:
            if conn:
                conn.close()  # Ensure connection is closed

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        conn = get_db_connection()
        if conn is None:
            flash("Failed to connect to the database")
            return redirect(url_for('signup'))

        try:
            email = request.form.get('email')
            password = request.form.get('password')
            role = 'user'  # Default role is 'user'

            # Validate required fields
            if not email or not password:
                flash("Email and password are required")
                return redirect(url_for('signup'))

            cursor = conn.cursor()

            # Insert the user into the 'users' table
            query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)"
            cursor.execute(query, (email, password, role))  # Store plain text password
            conn.commit()
            flash("User registered successfully!")  # Success message
            return redirect(url_for('login'))  # Redirect to login after successful signup

        except Error as e:
            print(f"Error while inserting user data: {e}")
            flash("Failed to register user", category="danger")
            return redirect(url_for('signup'))
        finally:
            if conn:
                conn.close()  # Ensure connection is closed

    return render_template('signup.html')

@app.route('/seller_registration', methods=['GET', 'POST'])
def seller_registration():
    if request.method == 'POST':
        conn = get_db_connection()
        if conn is None:
            flash("Failed to connect to the database", "danger")
            return redirect(url_for('seller_registration'))

        try:
            # Get form data
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            email = request.form.get('email')
            phone_number = request.form.get('phoneNumber')
            address = request.form.get('address')
            postal_code = request.form.get('postalCode')
            business_name = request.form.get('businessName')
            description = request.form.get('description')

            # Validate required fields
            if not first_name or not last_name or not email or not business_name:
                flash("First name, last name, email, and business name are required", "danger")
                return redirect(url_for('seller_registration'))

            cursor = conn.cursor()

            # Insert data into the 'sellers' table
            query = """
                INSERT INTO sellers (first_name, last_name, email, phone_number, address, postal_code, business_name, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (first_name, last_name, email, phone_number, address, postal_code, business_name, description))
            conn.commit()
            flash("Seller registered successfully!", "success")
            return redirect(url_for('home'))  # Redirect to home page after registration

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            return redirect(url_for('seller_registration'))
        finally:
            if conn:
                conn.close()  # Ensure connection is closed

    return render_template('seller_registration.html')

@app.route('/admin_page', methods=['GET'])
@login_required
def admin_page():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))
    return render_template('admin_page.html')

@app.route('/super_page', methods=['GET'])
@login_required
def super_page():
    if session.get('role') != 'superadmin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))
    return render_template('super_page.html')

@app.route('/user_page', methods=['GET'])
@login_required
def user_page():
    if session.get('role') != 'user':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))
    return render_template('user_page.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session on logout
    flash("Logged out successfully!", category="success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)  # Optional: Set debug=True for helpful error messages
