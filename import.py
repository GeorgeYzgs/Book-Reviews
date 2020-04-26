import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Sets up Database, this is a different app within our project so no reason to import it.
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# By using the csv reader we have to skip the first line headers
with open("books.csv", mode='r') as file:
    reader = csv.reader(file)
    next(reader)
    for isbn, title, author, year in reader:
        # print(isbn, title, author, year)
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": isbn,
                    "title": title,
                    "author": author,
                    "year": year})
    db.commit()
