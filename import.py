import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(
    "postgres://aigpbdyoxbwzjl:a88f1dbaca1b4b3f421c70e9ecce974162164c0e20e930cb0ce68f37ad80aa16@ec2-54-162-119-125.compute-1.amazonaws.com:5432/d7jd4p47r9c69")
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        print(
            f"Added in books table title: {title}, author: {author}, year: {year}.")
    db.commit()


if __name__ == "__main__":
    main()
