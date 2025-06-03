import sqlite3
import os

def reset_database():
    """
    Delete the existing database and create a fresh one with correct schema
    WARNING: This will delete all existing data!
    """
    db_file = "expense_tracker.db"
    
    # Delete existing database file
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✅ Deleted existing database: {db_file}")
    else:
        print(f"ℹ️ Database file {db_file} doesn't exist")
    
    # Create fresh database with correct schema
    print("🔄 Creating fresh database with multi-user support...")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create users table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created users table")
    
    # Create expenses table with user_id
    cursor.execute('''
    CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        category TEXT NOT NULL,
        description TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        payment_method TEXT DEFAULT 'Cash',
        recurring BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    print("✅ Created expenses table with user_id foreign key")
    
    # Create categories table
    cursor.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        budget REAL DEFAULT 0,
        color TEXT DEFAULT '#FF6B6B',
        icon TEXT DEFAULT '💰',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("✅ Created categories table")
    
    # Create payment_methods table
    cursor.execute('''
    CREATE TABLE payment_methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT DEFAULT 'Cash'
    )
    ''')
    print("✅ Created payment_methods table")
    
    # Insert default categories
    default_categories = [
        ("Food", 300, "#FF6B6B", "🍔"),
        ("Transportation", 150, "#4ECDC4", "🚗"),
        ("Housing", 800, "#45B7D1", "🏠"),
        ("Entertainment", 200, "#96CEB4", "🎬"),
        ("Utilities", 250, "#FFE6A7", "⚡"),
        ("Healthcare", 200, "#D3D3D3", "🏥"),
        ("Shopping", 300, "#FFB6C1", "🛍️"),
        ("Education", 150, "#87CEEB", "📚"),
        ("Others", 100, "#D3D3D3", "💼")
    ]
    cursor.executemany(
        "INSERT INTO categories (name, budget, color, icon) VALUES (?, ?, ?, ?)",
        default_categories
    )
    print("✅ Inserted default categories")
    
    # Insert default payment methods
    default_payments = [
        ("Cash", "Cash"),
        ("Credit Card", "Card"),
        ("Debit Card", "Card"),
        ("Bank Transfer", "Digital"),
        ("Mobile Payment", "Digital"),
        ("Check", "Other")
    ]
    cursor.executemany(
        "INSERT INTO payment_methods (name, type) VALUES (?, ?)",
        default_payments
    )
    print("✅ Inserted default payment methods")
    
    conn.commit()
    conn.close()
    
    print("🎉 Database reset complete! Multi-user support is now active.")
    print("📝 You can now run your Streamlit app with: streamlit run your_app.py")

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL existing data!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        reset_database()
    else:
        print("❌ Database reset cancelled.")
