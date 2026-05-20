from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import joblib

# PDF LIBRARIES
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = "hybridmlsecret"

# =========================
# LOAD ML MODELS
# =========================

expense_model = joblib.load("models/expense_model.pkl")
cluster_model = joblib.load("models/savings_cluster.pkl")
encoder = joblib.load("models/encoder.pkl")

# =========================
# DATABASE CONNECTION
# =========================

def connect_db():
    conn = sqlite3.connect("database.db")
    return conn

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    if 'user' in session:
        return redirect('/dashboard')

    return render_template("login.html")

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if 'user' in session:
        return redirect('/dashboard')

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()

        # CREATE TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)

        # CHECK EXISTING USER
        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        existing_user = cur.fetchone()

        if existing_user:
            conn.close()
            return "Email Already Registered"

        # INSERT USER
        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        session['user'] = name

        return redirect('/dashboard')

    return render_template("register.html")

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['POST'])
def login():

    if 'user' in session:
        return redirect('/dashboard')

    email = request.form['email']
    password = request.form['password']

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cur.fetchone()

    conn.close()

    if user:
        session['user'] = user[1]
        return redirect('/dashboard')

    return "Invalid Email or Password"

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    return render_template(
        "dashboard.html",

        prediction=session.get('prediction', 0),
        savings=session.get('savings', 0),
        group=session.get('group', "No Data"),

        house_rent=session.get('house_rent', 0),
        electricity_bill=session.get('electricity_bill', 0),
        grocery_bill=session.get('grocery_bill', 0),
        transport_bill=session.get('transport_bill', 0),
        medical_bill=session.get('medical_bill', 0),
        entertainment_bill=session.get('entertainment_bill', 0),
        other_expense=session.get('other_expense', 0)
    )

# =========================
# PREDICTION PAGE
# =========================

@app.route('/prediction')
def prediction_page():

    if 'user' not in session:
        return redirect('/')

    return render_template("prediction.html")

# =========================
# PREDICT FUNCTION
# =========================

@app.route('/predict', methods=['POST'])
def predict():

    if 'user' not in session:
        return redirect('/')

    try:

        salary = int(request.form['salary'])
        family = int(request.form['family'])
        district = request.form['district']

        # SALARY VALIDATION

        if salary < 6000:

            return render_template(
                "prediction.html",
                error="⚠ Salary must be greater than 6000"
            )

        # DISTRICT ENCODING

        district_encoded = encoder.transform([district])[0]

        # EXPENSE PREDICTION

        total_expense = expense_model.predict(
            [[salary, family, district_encoded]]
        )[0]

        total_expense = round(total_expense, 2)

        # EXPENSE BREAKDOWN

        house_rent = round(total_expense * 0.35, 2)
        electricity_bill = round(total_expense * 0.10, 2)
        grocery_bill = round(total_expense * 0.20, 2)
        transport_bill = round(total_expense * 0.10, 2)
        medical_bill = round(total_expense * 0.10, 2)
        entertainment_bill = round(total_expense * 0.05, 2)
        other_expense = round(total_expense * 0.10, 2)

        savings = round(salary - total_expense, 2)

        # CLUSTER PREDICTION

        cluster = cluster_model.predict(
            [[salary, total_expense, savings]]
        )[0]

        if cluster == 0:
            group = "Low Saver"

        elif cluster == 1:
            group = "Medium Saver"

        else:
            group = "High Saver"

        # STORE SESSION DATA

        session['prediction'] = total_expense
        session['savings'] = savings
        session['group'] = group

        session['house_rent'] = house_rent
        session['electricity_bill'] = electricity_bill
        session['grocery_bill'] = grocery_bill
        session['transport_bill'] = transport_bill
        session['medical_bill'] = medical_bill
        session['entertainment_bill'] = entertainment_bill
        session['other_expense'] = other_expense

        return redirect('/dashboard')

    except Exception as e:
        return f"Error: {e}"

# =========================
# SAVINGS PAGE
# =========================

@app.route('/savings')
def savings():

    if 'user' not in session:
        return redirect('/')

    return render_template(
        "savings.html",
        savings=session.get('savings', 0),
        group=session.get('group', "No Group")
    )

# =========================
# VISUALIZATION
# =========================

@app.route('/visualization')
def visualization():

    if 'user' not in session:
        return redirect('/')

    return render_template(
        "visualization.html",

        prediction=session.get('prediction', 0),
        savings=session.get('savings', 0),

        house_rent=session.get('house_rent', 0),
        electricity_bill=session.get('electricity_bill', 0),
        grocery_bill=session.get('grocery_bill', 0),
        transport_bill=session.get('transport_bill', 0),
        medical_bill=session.get('medical_bill', 0),
        entertainment_bill=session.get('entertainment_bill', 0),
        other_expense=session.get('other_expense', 0)
    )

# =========================
# PROFILE PAGE
# =========================

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT name,email FROM users WHERE name=?",
        (session['user'],)
    )

    user = cur.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        name=user[0],
        email=user[1]
    )

# =========================
# UPDATE PROFILE
# =========================

@app.route('/update_profile', methods=['POST'])
def update_profile():

    if 'user' not in session:
        return redirect('/')

    name = request.form['name']
    email = request.form['email']

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET name=?, email=?
        WHERE name=?
    """, (name, email, session['user']))

    conn.commit()
    conn.close()

    session['user'] = name

    return redirect('/profile')

# =========================
# CHANGE PASSWORD
# =========================

@app.route('/change_password', methods=['POST'])
def change_password():

    if 'user' not in session:
        return redirect('/')

    new_password = request.form['new_password']

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET password=?
        WHERE name=?
    """, (new_password, session['user']))

    conn.commit()
    conn.close()

    return redirect('/profile')

# =========================
# ADMIN DASHBOARD
# =========================

@app.route('/admin')
def admin():

    if 'user' not in session:
        return redirect('/')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    conn.close()

    return render_template(
        "admin.html",

        users=users,

        prediction=session.get('prediction', 0),
        savings=session.get('savings', 0),
        group=session.get('group', "No Data")
    )

# =========================
# DELETE USER
# =========================

@app.route('/delete_user/<int:id>')
def delete_user(id):

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/admin')

# =========================
# PDF REPORT GENERATOR
# =========================

@app.route('/download_report')
def download_report():

    if 'user' not in session:
        return redirect('/')

    # PDF FILE NAME

    file_path = "prediction_report.pdf"

    # CREATE PDF

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()
    elements = []

    # TITLE

    title = Paragraph(
        "Hybrid ML Prediction & Savings Report",
        styles['Title']
    )

    elements.append(title)
    elements.append(Spacer(1, 20))

    # USER DETAILS

    user_text = Paragraph(
        f"<b>User:</b> {session['user']}",
        styles['BodyText']
    )

    elements.append(user_text)
    elements.append(Spacer(1, 10))

    # REPORT DATA

    prediction = session.get('prediction', 0)
    savings = session.get('savings', 0)
    group = session.get('group', 'No Data')

    data = [

        f"Total Expense : ₹ {prediction}",
        f"Savings : ₹ {savings}",
        f"Savings Group : {group}",
        f"House Rent : ₹ {session.get('house_rent', 0)}",
        f"Electricity Bill : ₹ {session.get('electricity_bill', 0)}",
        f"Grocery Bill : ₹ {session.get('grocery_bill', 0)}",
        f"Transport Bill : ₹ {session.get('transport_bill', 0)}",
        f"Medical Bill : ₹ {session.get('medical_bill', 0)}",
        f"Entertainment Bill : ₹ {session.get('entertainment_bill', 0)}",
        f"Other Expense : ₹ {session.get('other_expense', 0)}"

    ]

    for item in data:

        paragraph = Paragraph(item, styles['BodyText'])

        elements.append(paragraph)
        elements.append(Spacer(1, 10))

    # FINAL MESSAGE

    final_text = Paragraph(
        "Generated using Hybrid Machine Learning Financial Prediction System.",
        styles['Italic']
    )

    elements.append(final_text)

    # BUILD PDF

    doc.build(elements)

    return send_file(
        file_path,
        as_attachment=True
    )

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# =========================
# RUN APP
# =========================

if __name__ == '__main__':
    app.run(debug=True)