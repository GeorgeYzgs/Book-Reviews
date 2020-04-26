from werkzeug.security import check_password_hash
from flask import flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

# Set up database, moved to this file to avoid circular imports
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Validates user input upon registration.
def valid_register(username, password, password2):
    """Back - end Validation for registration"""

    # Ensure username was submitted
    if not username:
        flash("Must Provide Username!", "danger")
        return False

    # Ensure password was submitted
    elif not password:
        flash("Must Provide Password!", "danger")
        return False

    # Ensure second password was submitted
    elif not password2:
        flash("Must Provide Second Password to validate!", "danger")
        return False

    # Ensure username length is correct
    if len(username) < 4 or len(username) > 16:
        flash("Username length should be between 4 and 16 characters", 'danger')
        return False

    if len(password) < 4 or len(password) > 20:
        flash("Password length should be between 4 and 20 characters", 'danger')
        return False

    # Ensure username is available,  case folding makes the username case - insensitive
    rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": username.casefold()}).fetchone()
    if rows:
        flash("Username unavailable!", "danger")
        return False

    # Ensure the two given passwords match
    if password != password2:
        flash("Passwords do not match!", "danger")
        return False

    return True


# Validates user input as they attempt to login.
def valid_login(username, password):
    """"Back - end validation for login"""

    # Ensure username was submitted
    if not username:
        flash("Must Provide Username!", "danger")
        return False

    # Ensure password was submitted
    elif not password:
        flash("Must Provide Password!", "danger")
        return False

    # Query database for username, case folding makes the username case - insensitive
    rows = db.execute("SELECT * FROM users WHERE username = :username",
                      {"username": username.casefold()}).fetchone()

    # Ensure username exists and password is correct
    if not rows or not check_password_hash(rows["hash"], password):
        flash("Invalid username and/or password!", 'danger')
        return False

    # Remember which user has logged in
    session["user_id"] = rows["id"]
    return True


# Searches Database for books, based on isbn author or title
def results(criteria, book):
    if not criteria:
        flash("Must Provide Criteria!", "danger")
        return None

    if not book:
        flash("Must Provide Search Criteria", "danger")
        return None

    # Adding the i in LIKE makes the given parameter case insensitive
    book = "%" + book + "%"
    if criteria == "isbn":
        books = db.execute("SELECT * FROM books WHERE isbn iLIKE :book", {"book": book}).fetchall()
    elif criteria == "author":
        books = db.execute("SELECT * FROM books WHERE author iLIKE :book", {"book": book}).fetchall()
    else:
        books = db.execute("SELECT * FROM books WHERE title iLIKE :book", {"book": book}).fetchall()

    return books


# Validates user input before submitting a comment
def valid_comment(rating, context):
    # Back - end validation for reviews
    if not rating:
        flash("You must submit a valid rating", 'danger')
        return False

    if not context:
        flash("You must leave a comment", 'danger')
        return False

    if rating < 1 or rating > 5:
        flash("Invalid rating range", 'danger')
        return False

    return True
