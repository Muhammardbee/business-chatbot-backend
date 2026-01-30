# Add this at the top with your imports
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
import calendar

# =========================
# SESSION CONFIG
# =========================
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # for login sessions

# =========================
# LOGIN ROUTES
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db["users"].find_one({"username": username})

        if not user or not check_password_hash(user["password"], password):
            return "Invalid username or password!", 400

        # store session
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        session["role"] = user.get("role", "salesperson")

        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# DASHBOARD ROUTE
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    role = session.get("role")

    # Products
    products = list(products_col.find({}, {"name": 1, "quantity": 1, "price": 1, "_id": 0}))

    # Sales (orders) per month
    pipeline = [
        {"$match": {}},  # add filters later if needed
        {"$group": {
            "_id": {"month": {"$month": "$created_at"}},
            "total": {"$sum": "$total"}  # assuming each order document has 'total'
        }},
        {"$sort": {"_id.month": 1}}
    ]
    sales_data = list(orders_col.aggregate(pipeline))
    months = [calendar.month_abbr[d["_id"]["month"]] for d in sales_data]
    totals = [d["total"] for d in sales_data]

    # Payments (assuming 'status' and 'amount' fields)
    payments = list(orders_col.find({}, {"created_at": 1, "total": 1, "status": 1, "_id": 0}))

    return render_template("dashboard.html",
                           role=role,
                           products=products,
                           sales_months=months,
                           sales_totals=totals,
                           payments=payments)
