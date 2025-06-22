from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import math
from search_engine import SearchEngine, get_db_connection

app = Flask(__name__)
CORS(app)  

search_engine = SearchEngine()

# Main search endpoint

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    all_results = search_engine.search(query)
    
    # Limit to top 50 results
    limited_results = all_results[:50]
    total_results = len(all_results)
    
    return jsonify({
        "results": limited_results,
        "query": query,
        "total_results": total_results
    })

if __name__ == '__main__':
    search_engine.build_index()
    app.run(host='127.0.0.1', port=3001)
