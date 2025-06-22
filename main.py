""""
Main file for the search engine
Contains Database and Indexer classes

Group 37

Authors:
- Farhan Syed
- Zi Yue Anna Yang
- David Tanudin 

"""

import sqlite3
import re
from spider import crawl
from nltk.stem import PorterStemmer

# SQLite3 database
class Database:
    def __init__(self, db_name = "spider.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self): 
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                last_modified TEXT,
                size INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_url TEXT,
                child_url TEXT,
                FOREIGN KEY(parent_url) REFERENCES pages(url),
                FOREIGN KEY(child_url) REFERENCES pages(url)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS body_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT,
                word_id INTEGER,
                frequency INTEGER,
                FOREIGN KEY(page_url) REFERENCES pages(url),
                FOREIGN KEY(word_id) REFERENCES words(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS title_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT,
                word_id INTEGER,
                frequency INTEGER,
                FOREIGN KEY(page_url) REFERENCES pages(url),
                FOREIGN KEY(word_id) REFERENCES words(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS body_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT,
                word_id INTEGER,
                position INTEGER,
                FOREIGN KEY(page_url) REFERENCES pages(url),
                FOREIGN KEY(word_id) REFERENCES words(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS title_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_url TEXT,
                word_id INTEGER,
                position INTEGER,
                FOREIGN KEY(page_url) REFERENCES pages(url),
                FOREIGN KEY(word_id) REFERENCES words(id)
            )
        ''')

        self.conn.commit()


    def insert_page(self, url, title, content, last_modified, size):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pages (url, title, content, last_modified, size)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, title, content, last_modified, size))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass # For duplicates

    def insert_link(self, parent_url, child_url):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO links (parent_url, child_url)
                VALUES (?, ?)
            ''', (parent_url, child_url))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  

    def insert_body_keyword(self, page_url, word_id, frequency):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO body_keywords (page_url, word_id, frequency)
                VALUES (?, ?, ?)
            ''', (page_url, word_id, frequency))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def insert_title_keyword(self, page_url, word_id, frequency):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO title_keywords (page_url, word_id, frequency)
                VALUES (?, ?, ?)
            ''', (page_url, word_id, frequency))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def insert_body_keyword_with_positions(self, page_url, word_id, freq, positions):
        self.insert_body_keyword(page_url, word_id, freq)
        cursor = self.conn.cursor()
        for pos in positions:
            cursor.execute('INSERT INTO body_positions (page_url, word_id, position) VALUES (?, ?, ?)', (page_url, word_id, pos))
        self.conn.commit()

    def insert_title_keyword_with_positions(self, page_url, word_id, freq, positions):
        self.insert_title_keyword(page_url, word_id, freq)
        cursor = self.conn.cursor()
        for pos in positions:
            cursor.execute('INSERT INTO title_positions (page_url, word_id, position) VALUES (?, ?, ?)', (page_url, word_id, pos))
        self.conn.commit()

    def get_or_create_word_id(self, word):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM words WHERE word = ?', (word,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute('INSERT INTO words (word) VALUES (?)', (word,))
        self.conn.commit()
        return cursor.lastrowid

    def fetch_all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM pages')
        return cursor.fetchall()

    def fetch_links(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM links')
        return cursor.fetchall()

    def fetch_keywords(self, page_url):
        cursor = self.conn.cursor()
        cursor.execute('SELECT keyword, frequency FROM keywords WHERE page_url = ?', (page_url,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()

class Indexer:
    def __init__(self, database):
        self.database = database

    def index_page(self, url, title, content, last_modified, size):
        self.database.insert_page(url, title, content, last_modified, size)

    def index_link(self, parent_url, child_url):
        self.database.insert_link(parent_url, child_url)

    def index_keywords(self, page_url, content, stopwords, title=""):
        stemmer = PorterStemmer()

        def process(text):
            words = re.findall(r'\b\w+\b', text.lower())
            stemmed_positions = []
            for i, word in enumerate(words):
                if word not in stopwords:
                    stemmed_word = stemmer.stem(word)
                    stemmed_positions.append((stemmed_word, i))
            return stemmed_positions

        body_positions = process(content)
        title_positions = process(title)

        body_index = {}
        for word, pos in body_positions:
            body_index.setdefault(word, []).append(pos)

        title_index = {}
        for word, pos in title_positions:
            title_index.setdefault(word, []).append(pos)

        for word, positions in body_index.items():
            word_id = self.database.get_or_create_word_id(word)
            self.database.insert_body_keyword_with_positions(page_url, word_id, len(positions), positions)

        for word, positions in title_index.items():
            word_id = self.database.get_or_create_word_id(word)
            self.database.insert_title_keyword_with_positions(page_url, word_id, len(positions), positions)

def main():
    db = Database()
    indexer = Indexer(db)
    start_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'

    with open("stopwords.txt", "r", encoding="utf-8") as f:
        stopwords = [line.strip() for line in f if line.strip()]
    
    crawl(start_url, indexer, stopwords, max_pages=300)

if __name__ == '__main__':
    main()
