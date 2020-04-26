import os
import requests
from flask import Flask, session, render_template, request, redirect, flash, jsonify
from flask_session import Session
from helpers import login_required
from validators import valid_login, valid_register, db, results, valid_comment
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Read API key from environment variable
key = os.getenv("GOODREADS_KEY")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Home page to search for books"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        books = results(request.form.get('criteria'), (request.form.get('book')))
        if not books:
            flash("No such books were found!", 'danger')
            return redirect("/")

        flash("Books Loaded!", 'primary')
        return render_template("index.html", books=books)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not valid_register(request.form.get('username'), request.form.get("password"),
                              request.form.get("password2")):
            return redirect("/register")

        # Inserts user into db
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   {"username": request.form.get("username").casefold(),
                    "hash": generate_password_hash(request.form.get("password"))})
        db.commit()

        flash("Registered successfully!", 'success')
        # Redirect user to login page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not valid_login(request.form.get("username"), request.form.get("password")):
            return redirect('/login')

        flash("You have been logged in!", 'primary')
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    """Provides book page and reviews"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not valid_comment(int(request.form.get('rating')), request.form.get('context')):
            return redirect('/book/' + isbn)

        db.execute("INSERT INTO reviews (user_id, book_id, rating, context) \
                    VALUES (:id, :book_id, :rating, :context)",
                   {"id": session['user_id'], "book_id": request.form.get('book_id'),
                    "rating": request.form.get('rating'), "context": request.form.get('context')})
        db.commit()
        flash("Review submitted!", 'success')
        return redirect("/book/" + isbn)

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Query our database for book information and reviews
        book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

        reviews = db.execute("SELECT users.id, username, context, rating, \
                              to_char(timestamp, 'DD Mon YY - HH24:MI:SS') as time \
                              FROM users JOIN reviews ON users.id=reviews.user_id \
                              WHERE book_id = :id ORDER BY time DESC", {"id": book_info[0]}).fetchall()

        # Checks if logged user has reviewed this book
        comment = False
        for review in reviews:
            if review['id'] == session['user_id']:
                comment = True

        print(comment)
        # Query Goodreads API with the given isbn for the book's reviews
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                             params={"key": key, "isbns": isbn}).json()
        goodreads = query['books'][0]

        return render_template("book.html", book=book_info, goodreads=goodreads, reviews=reviews, comment=comment)


@app.route("/api/<isbn>", methods=['GET'])
def api_call(isbn):
    """We create our api for others to use, no login will be required"""

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                     {"isbn": isbn}).fetchone()

    # Error checking for valid ISBN
    if not row:
        return jsonify({"Error": "ISBN not found"}), 404

    # Convert to dictionary
    result = dict(row.items())

    # Changes average score to just 2 decimal points
    result['average_score'] = float('%.2f' % (result['average_score']))
    return jsonify(result)


if __name__ == '__main__':
    app.run()
