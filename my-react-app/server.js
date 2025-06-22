const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3001;

// Enable CORS for all routes
app.use(cors());
app.use(express.json());

// Connect to the SQLite database
const db = new sqlite3.Database('./spider.db', (err) => {
  if (err) {
    console.error('Error connecting to database:', err.message);
  } else {
    console.log('Connected to the SQLite database.');
    
    // Log database tables for debugging
    db.all("SELECT name FROM sqlite_master WHERE type='table'", [], (err, tables) => {
      if (err) {
        console.error('Error fetching tables:', err.message);
      } else {
        console.log('Database tables:', tables);
      }
    });
  }
});

// Get all tables in the database
app.get('/api/tables', (req, res) => {
  const query = `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';`;
  
  db.all(query, [], (err, tables) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ tables });
  });
});

// Get all data from a specific table
app.get('/api/table/:tableName', (req, res) => {
  const tableName = req.params.tableName;
  const query = `SELECT * FROM ${tableName};`;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ data: rows });
  });
});

// Get table schema
app.get('/api/schema/:tableName', (req, res) => {
  const tableName = req.params.tableName;
  const query = `PRAGMA table_info(${tableName});`;
  
  db.all(query, [], (err, columns) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ schema: columns });
  });
});

// Custom query endpoint
app.post('/api/query', (req, res) => {
  const { query, params = [] } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: 'Query is required' });
  }
  
  db.all(query, params, (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ data: rows });
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

// Close the database connection when the server is terminated
process.on('SIGINT', () => {
  db.close((err) => {
    if (err) {
      console.error(err.message);
    }
    console.log('Database connection closed.');
    process.exit(0);
  });
});
