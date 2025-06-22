const sqlite3 = require('sqlite3').verbose();

// Connect to the database
const db = new sqlite3.Database('./spider.db', (err) => {
  if (err) {
    console.error('Error connecting to database:', err.message);
    process.exit(1);
  }
  console.log('Connected to the SQLite database.');
});

// Get all tables
db.all("SELECT name FROM sqlite_master WHERE type='table'", [], (err, tables) => {
  if (err) {
    console.error('Error fetching tables:', err.message);
    return;
  }
  
  console.log('Tables in the database:');
  if (tables.length === 0) {
    console.log('No tables found.');
  } else {
    tables.forEach(table => {
      console.log(`- ${table.name}`);
      
      // Get schema for each table
      db.all(`PRAGMA table_info(${table.name})`, [], (err, columns) => {
        if (err) {
          console.error(`Error fetching schema for table ${table.name}:`, err.message);
          return;
        }
        
        console.log(`\nSchema for table ${table.name}:`);
        columns.forEach(column => {
          console.log(`  ${column.name} (${column.type})${column.pk ? ' PRIMARY KEY' : ''}${column.notnull ? ' NOT NULL' : ''}`);
        });
        
        // Get sample data for each table
        db.all(`SELECT * FROM ${table.name} LIMIT 5`, [], (err, rows) => {
          if (err) {
            console.error(`Error fetching data from table ${table.name}:`, err.message);
            return;
          }
          
          console.log(`\nSample data from table ${table.name} (up to 5 rows):`);
          if (rows.length === 0) {
            console.log('  No data found.');
          } else {
            console.log(JSON.stringify(rows, null, 2));
          }
          
          // If this is the last table, close the database connection
          if (table.name === tables[tables.length - 1].name) {
            db.close((err) => {
              if (err) {
                console.error('Error closing database:', err.message);
              } else {
                console.log('\nDatabase connection closed.');
              }
            });
          }
        });
      });
    });
  }
});
