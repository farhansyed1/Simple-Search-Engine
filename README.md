# Simple-Search-Engine
### Requirements
The code has been built using Python 3.12 but it should work with other versions as well.

### Running the program
To run the code, first ensure you navigate to the correct folder containing main.py, flask_server.py, spider.py etc.  Then enter the following commands step by step in your terminal:

1. Install necessary packages: pip install -r requirements.txt 
2. Create the database: python main.py
3. Run the server: python flask_server.py

Open a new terminal and navigate into the correct folder called "my-react-app" and type in following command in the new terminal: 

4. Start the npm environment: npm run dev

Your default browser should automatically open a new tab with the search engine's URL, which is http://localhost:XXXX

### Files
- main.py: Contains the Database and Indexer classes, as well as the main function. 
- spider.py: Contains the crawler
- flask_server.py: Contains the flask server code
- search_engine.py: Contains the logic for the search engine
- stopwords.txt: Contains the stopwords
- my_react-app: Folder containing code for frontend
