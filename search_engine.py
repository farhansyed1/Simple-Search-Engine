import sqlite3
import re
import math
from collections import defaultdict, Counter

import os

def get_db_connection():
    # Get the absolute path to the spider.db file in the parent directory
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'spider.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_stopwords():
    try:
        with open("stopwords.txt", "r", encoding="utf-8") as f:
            return set([line.strip() for line in f if line.strip()])
    except FileNotFoundError:
        print("Stopwords file not found!")
        return set()
    
STOPWORDS = load_stopwords()

def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def preprocess_text(text, remove_stopwords=True):
    tokens = tokenize(text)
    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOPWORDS]
    return tokens

def extract_phrases(query):
    phrases = re.findall(r'"([^"]*)"', query)
    remaining_query = re.sub(r'"[^"]*"', '', query)
    return phrases, remaining_query

class SearchEngine:
    def __init__(self):
        self.inverted_index = defaultdict(list)
        self.document_vectors = {}
        self.document_lengths = {}
        self.max_tf = {}
        self.idf = {}
        self.documents = {}
        self.title_boost = 3.0  
        
    def build_index(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, url, title, content FROM pages")
        documents = cursor.fetchall()
        
        for doc in documents:
            doc_id, url, title, content = doc['id'], doc['url'], doc['title'], doc['content']
            self.documents[doc_id] = {'url': url, 'title': title, 'content': content}
            
            title_tokens = preprocess_text(title or "")
            content_tokens = preprocess_text(content or "")
            
            all_tokens = title_tokens * int(self.title_boost) + content_tokens
            
            term_freq = Counter(all_tokens)
            self.max_tf[doc_id] = max(term_freq.values()) if term_freq else 1
            
            for term, freq in term_freq.items():
                self.inverted_index[term].append((doc_id, freq))
        
        num_docs = len(documents)
        for term, postings in self.inverted_index.items():
            self.idf[term] = math.log(num_docs / len(postings))
        
        for doc_id in self.documents:
            self.document_vectors[doc_id] = self.calculate_document_vector(doc_id)
            self.document_lengths[doc_id] = self.calculate_vector_length(self.document_vectors[doc_id])
        
        conn.close()
        
    def calculate_document_vector(self, doc_id):
        vector = {}
        for term, postings in self.inverted_index.items():
            for d_id, freq in postings:
                if d_id == doc_id:
                    vector[term] = (freq / self.max_tf[doc_id]) * self.idf[term]
        return vector
    
    def calculate_vector_length(self, vector):
        return math.sqrt(sum(w * w for w in vector.values()))
    
    def calculate_query_vector(self, query_terms):
        query_tf = Counter(query_terms)
        query_max_tf = max(query_tf.values()) if query_tf else 1
        
        query_vector = {}
        for term, freq in query_tf.items():
            if term in self.idf:  
                query_vector[term] = (freq / query_max_tf) * self.idf[term]
        
        return query_vector
    
    def cosine_similarity(self, query_vector, doc_id):
        doc_vector = self.document_vectors[doc_id]
        
        dot_product = 0
        for term, weight in query_vector.items():
            if term in doc_vector:
                dot_product += weight * doc_vector[term]
        
        query_length = math.sqrt(sum(w * w for w in query_vector.values()))
        doc_length = self.document_lengths[doc_id]
        
        if query_length == 0 or doc_length == 0:
            return 0
        
        return dot_product / (query_length * doc_length)
    
    def check_phrase_match(self, phrase, doc_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        words = preprocess_text(phrase)
        if not words:
            return 0

        word_ids = []
        for word in words:
            cursor.execute("SELECT id FROM words WHERE word = ?", (word,))
            row = cursor.fetchone()
            if not row:
                return 0  
            word_ids.append(row['id'])

        def has_phrase_match(table):
            pos_lists = []
            for wid in word_ids:
                cursor.execute(f'''
                    SELECT position FROM {table}
                    WHERE page_url = (SELECT url FROM pages WHERE id = ?)
                    AND word_id = ?
                ''', (doc_id, wid))
                pos_lists.append([row['position'] for row in cursor.fetchall()])

            if not all(pos_lists):
                return False

            first_positions = pos_lists[0]
            for start in first_positions:
                if all((start + i) in pos_lists[i] for i in range(1, len(pos_lists))):
                    return True
            return False

        match_score = 0
        if has_phrase_match("title_positions"):
            match_score += self.title_boost
        if has_phrase_match("body_positions"):
            match_score += 1.0

        conn.close()
        return match_score

    def search(self, query):
        phrases, remaining_query = extract_phrases(query)
        query_terms = preprocess_text(remaining_query)
        
        for phrase in phrases:
            query_terms.extend(preprocess_text(phrase))
        
        query_vector = self.calculate_query_vector(query_terms)
        
        results = []
        for doc_id in self.documents:
            similarity = self.cosine_similarity(query_vector, doc_id)
            
            phrase_boost = 0
            for phrase in phrases:
                phrase_boost += self.check_phrase_match(phrase, doc_id)
            
            final_score = similarity + (similarity * phrase_boost)
            
            if final_score > 0:
                results.append((doc_id, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        formatted_results = []
        for doc_id, score in results:
            doc = self.documents[doc_id]
            content = doc['content'] or ""
            snippet = content[:200] + "..." if len(content) > 200 else content
            
            # Get page size from database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT size FROM pages WHERE id = ?", (doc_id,))
            size_row = cursor.fetchone()
            size = size_row['size'] if size_row else 0
            
            cursor.execute("""
                SELECT w.word, bk.frequency
                FROM words w
                JOIN body_keywords bk ON w.id = bk.word_id
                WHERE bk.page_url = (SELECT url FROM pages WHERE id = ?)
                ORDER BY bk.frequency DESC
                LIMIT 10
            """, (doc_id,))
            keywords = [{'word': row['word'], 'frequency': row['frequency']} for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT parent_url FROM links
                WHERE child_url = (SELECT url FROM pages WHERE id = ?)
            """, (doc_id,))
            parent_links = [row['parent_url'] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT child_url FROM links
                WHERE parent_url = (SELECT url FROM pages WHERE id = ?)
            """, (doc_id,))
            child_links = [row['child_url'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT last_modified FROM pages WHERE id = ?", (doc_id,))
            last_modified_row = cursor.fetchone()
            last_modified = last_modified_row['last_modified'] if last_modified_row else "Unknown"
            
            conn.close()
            
            formatted_results.append({
                'id': doc_id,
                'url': doc['url'],
                'title': doc['title'] or "No Title",
                'snippet': snippet,
                'score': score,
                'size': size,
                'keywords': keywords,
                'parent_links': parent_links,
                'child_links': child_links,
                'last_modified': last_modified
            })
        
        return formatted_results
