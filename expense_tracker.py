import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import hashlib
import os
from typing import Optional, List, Tuple

# --- Configuration ---
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Setup ---
def init_db():
    """Initialize database with all required tables and default data"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
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
    
    # Create categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        budget REAL DEFAULT 0,
        color TEXT DEFAULT '#FF6B6B',
        icon TEXT DEFAULT '💰',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create payment_methods table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT DEFAULT 'Cash'
    )
    ''')
    
    # Insert default data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
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
    
    cursor.execute("SELECT COUNT(*) FROM payment_methods")
    if cursor.fetchone()[0] == 0:
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
    
    conn.commit()
    conn.close()

# --- Helper Functions ---
def get_categories() -> List[str]:
    """Get all category names"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

def get_payment_methods() -> List[str]:
    """Get all payment method names"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM payment_methods ORDER BY name")
    methods = [row[0] for row in cursor.fetchall()]
    conn.close()
    return methods

def get_user_id(username: str) -> Optional[int]:
    """Get user ID by username"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_expenses(user_id: int, query: str = None, params: List = None) -> pd.DataFrame:
    """Get expenses with optional custom query"""
    conn = sqlite3.connect("expense_tracker.db")
    try:
        if query is None:
            query = "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC"
            df = pd.read_sql(query, conn, params=[user_id])
        else:
            all_params = [user_id] + (params or [])
            df = pd.read_sql(query, conn, params=all_params)
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame(columns=['id', 'user_id', 'date', 'amount', 'category', 'description', 'tags', 'payment_method', 'recurring'])
    finally:
        conn.close()

def add_expense(user_id: int, date: str, amount: float, category: str, 
               description: str, tags: str, payment_method: str, recurring: bool) -> bool:
    """Add new expense"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO expenses (user_id, date, amount, category, description, tags, payment_method, recurring)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, date, amount, category, description, tags, payment_method, int(recurring))
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False
    finally:
        conn.close()

def update_expense(user_id: int, expense_id: int, date: str, amount: float, 
                  category: str, description: str, tags: str, payment_method: str, recurring: bool) -> bool:
    """Update existing expense"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE expenses
            SET date = ?, amount = ?, category = ?, description = ?, tags = ?, payment_method = ?, recurring = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (date, amount, category, description, tags, payment_method, int(recurring), expense_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error updating expense: {str(e)}")
        return False
    finally:
        conn.close()

def delete_expense(user_id: int, expense_id: int) -> bool:
    """Delete expense"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False
    finally:
        conn.close()

# --- Authentication Functions ---
def create_user(username: str, password: str) -> bool:
    """Create new user"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[int]:
    """Authenticate user and return user ID"""
    conn = sqlite3.connect("expense_tracker.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None
    finally:
        conn.close()

# --- Analytics Functions ---
def get_monthly_summary(user_id: int) -> Tuple[float, float, int]:
    """Get current and previous month totals and transaction count"""
    conn = sqlite3.connect("expense_tracker.db")
    try:
        current_month = datetime.now().strftime("%Y-%m")
        last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id = ? AND date LIKE ?",
            (user_id, f"{current_month}%")
        )
        current_result = cursor.fetchone()
        current_total = current_result[0] or 0
        current_count = current_result[1] or 0
        
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date LIKE ?",
            (user_id, f"{last_month}%")
        )
        last_total = cursor.fetchone()[0] or 0
        
        return current_total, last_total, current_count
    except Exception as e:
        st.error(f"Error calculating monthly summary: {str(e)}")
        return 0, 0, 0
    finally:
        conn.close()

def get_budget_performance(user_id: int) -> pd.DataFrame:
    """Get budget vs actual spending for current month"""
    current_month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect("expense_tracker.db")
    try:
        query = """
        SELECT c.name, c.budget, c.color, c.icon, COALESCE(SUM(e.amount), 0) as spent
        FROM categories c
        LEFT JOIN expenses e ON c.name = e.category AND e.date LIKE ? AND e.user_id = ?
        GROUP BY c.name, c.budget, c.color, c.icon
        ORDER BY c.name
        """
        df = pd.read_sql(query, conn, params=[f"{current_month}%", user_id])
        if not df.empty:
            df['remaining'] = df['budget'] - df['spent']
            df['percentage'] = (df['spent'] / df['budget'] * 100).round(1)
            df['status'] = df.apply(lambda x: 'Over Budget' if x['remaining'] < 0 else 'Within Budget', axis=1)
        return df
    except Exception as e:
        st.error(f"Error loading budget performance: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_category_spending(user_id: int, days: int = 30) -> pd.DataFrame:
    """Get spending by category for last N days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("expense_tracker.db")
    try:
        query = """
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND date >= ?
        GROUP BY category
        ORDER BY total DESC
        """
        df = pd.read_sql(query, conn, params=[user_id, start_date])
        return df
    except Exception as e:
        st.error(f"Error loading category spending: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- UI Components ---
def render_dashboard(user_id: int):
    """Render dashboard with key metrics and charts"""
    st.header("📊 Dashboard")
    
    # Monthly summary
    current_total, last_total, current_count = get_monthly_summary(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("This Month", f"₹{current_total:,.2f}", 
                 delta=f"₹{current_total - last_total:,.2f}" if last_total > 0 else None)
    with col2:
        st.metric("Last Month", f"₹{last_total:,.2f}")
    with col3:
        st.metric("Transactions", f"{current_count}")
    with col4:
        avg_transaction = current_total / current_count if current_count > 0 else 0
        st.metric("Avg Transaction", f"₹{avg_transaction:,.2f}")
    
    # Budget performance
    st.subheader("💰 Budget Performance")
    budget_df = get_budget_performance(user_id)
    if not budget_df.empty:
        # Budget chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Budget',
            x=budget_df['name'],
            y=budget_df['budget'],
            marker_color='lightblue',
            opacity=0.7
        ))
        fig.add_trace(go.Bar(
            name='Spent',
            x=budget_df['name'],
            y=budget_df['spent'],
            marker_color=['red' if x < 0 else 'green' for x in budget_df['remaining']]
        ))
        fig.update_layout(
            title="Budget vs Actual Spending",
            xaxis_title="Category",
            yaxis_title="Amount (₹)",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Budget table
        display_df = budget_df[['name', 'budget', 'spent', 'remaining', 'percentage', 'status']].copy()
        display_df.columns = ['Category', 'Budget', 'Spent', 'Remaining', '%', 'Status']
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No budget data available.")
    
    # Category spending chart
    st.subheader("📈 Category Spending (Last 30 Days)")
    category_df = get_category_spending(user_id, 30)
    if not category_df.empty:
        fig = px.pie(category_df, values='total', names='category', 
                    title="Spending by Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No spending data available.")

def render_add_expense(user_id: int):
    """Render add expense form"""
    st.header("➕ Add Expense")
    
    with st.form("add_expense", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", value=datetime.now())
            amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01, format="%.2f")
            category = st.selectbox("Category", get_categories())
            payment_method = st.selectbox("Payment Method", get_payment_methods())
        
        with col2:
            description = st.text_input("Description")
            tags = st.text_input("Tags (comma-separated)")
            recurring = st.checkbox("Recurring Expense")
            st.write("")  # Spacing
        
        submitted = st.form_submit_button("Add Expense", type="primary")
        
        if submitted:
            if amount > 0:
                if add_expense(user_id, date.strftime("%Y-%m-%d"), amount, category, 
                             description, tags, payment_method, recurring):
                    st.success("✅ Expense added successfully!")
                    st.rerun()
            else:
                st.error("Amount must be greater than 0")

def render_expense_list(user_id: int):
    """Render expense list with filters and edit/delete functionality"""
    st.header("📋 Expense List")
    
    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox("Category", ["All"] + get_categories())
            payment_filter = st.selectbox("Payment Method", ["All"] + get_payment_methods())
        with col2:
            date_from = st.date_input("From", value=datetime.now() - timedelta(days=30))
            date_to = st.date_input("To", value=datetime.now())
        with col3:
            min_amount = st.number_input("Min Amount", min_value=0.0, value=0.0)
            max_amount = st.number_input("Max Amount", min_value=0.0, value=0.0)
        
        apply_filters = st.button("Apply Filters", type="primary")
    
    # Build query based on filters
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = []
    
    if apply_filters:
        if category_filter != "All":
            query += " AND category = ?"
            params.append(category_filter)
        if payment_filter != "All":
            query += " AND payment_method = ?"
            params.append(payment_filter)
        if date_from:
            query += " AND date >= ?"
            params.append(date_from.strftime("%Y-%m-%d"))
        if date_to:
            query += " AND date <= ?"
            params.append(date_to.strftime("%Y-%m-%d"))
        if min_amount > 0:
            query += " AND amount >= ?"
            params.append(min_amount)
        if max_amount > 0:
            query += " AND amount <= ?"
            params.append(max_amount)
    
    query += " ORDER BY date DESC, id DESC"
    
    # Get expenses
    df = get_expenses(user_id, query if apply_filters else None, params if apply_filters else None)
    
    if not df.empty:
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Expenses", len(df))
        with col2:  
            st.metric("Total Amount", f"₹{df['amount'].sum():,.2f}")
        with col3:
            st.metric("Average", f"₹{df['amount'].mean():,.2f}")
        
        # Display table
        display_df = df[['id', 'date', 'category', 'amount', 'description', 'payment_method']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
        
        # Edit/Delete section
        st.subheader("✏️ Edit/Delete Expense")
        expense_id = st.number_input("Enter Expense ID", min_value=1, step=1, key="edit_id")
        
        if expense_id and expense_id in df['id'].values:
            expense = df[df['id'] == expense_id].iloc[0]
            
            with st.form("edit_expense"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_date = st.date_input("Date", value=datetime.strptime(expense['date'], "%Y-%m-%d"))
                    edit_amount = st.number_input("Amount", value=float(expense['amount']), min_value=0.01)
                    edit_category = st.selectbox("Category", get_categories(), 
                                               index=get_categories().index(expense['category']))
                    edit_payment = st.selectbox("Payment Method", get_payment_methods(),
                                              index=get_payment_methods().index(expense['payment_method']))
                
                with col2:
                    edit_description = st.text_input("Description", value=str(expense['description']))
                    edit_tags = st.text_input("Tags", value=str(expense['tags']))
                    edit_recurring = st.checkbox("Recurring", value=bool(expense['recurring']))
                
                col1, col2 = st.columns(2)
                update_btn = col1.form_submit_button("Update", type="primary")
                delete_btn = col2.form_submit_button("Delete", type="secondary")
                
                if update_btn:
                    if update_expense(user_id, expense_id, edit_date.strftime("%Y-%m-%d"),
                                    edit_amount, edit_category, edit_description, edit_tags,
                                    edit_payment, edit_recurring):
                        st.success("✅ Expense updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update expense")
                
                if delete_btn:
                    if delete_expense(user_id, expense_id):
                        st.success("🗑️ Expense deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete expense")
        
        elif expense_id:
            st.error("Expense ID not found")
    
    else:
        st.info("No expenses found matching the criteria.")

def render_reports(user_id: int):
    """Render reports and analytics"""
    st.header("📊 Reports & Analytics")
    
    report_type = st.selectbox("Select Report Type", 
                              ["Monthly Trends", "Category Analysis", "Payment Method Analysis", "Spending Patterns"])
    
    if report_type == "Monthly Trends":
        st.subheader("📈 Monthly Spending Trends")
        months = st.slider("Number of months", 3, 12, 6)
        
        conn = sqlite3.connect("expense_tracker.db")
        query = """
        SELECT DATE(date, 'start of month') as month, 
               SUM(amount) as total,
               COUNT(*) as transactions
        FROM expenses 
        WHERE user_id = ? AND date >= date('now', '-' || ? || ' months')
        GROUP BY month
        ORDER BY month
        """
        df = pd.read_sql(query, conn, params=[user_id, months])
        conn.close()
        
        if not df.empty:
            fig = px.line(df, x='month', y='total', title='Monthly Spending Trend',
                         markers=True, line_shape='spline')
            fig.update_layout(xaxis_title='Month', yaxis_title='Amount (₹)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly breakdown
            df['month'] = pd.to_datetime(df['month']).dt.strftime('%B %Y')
            df['total'] = df['total'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available for the selected period.")
    
    elif report_type == "Category Analysis":
        st.subheader("🏷️ Category Analysis")
        period = st.selectbox("Time Period", ["Last 30 days", "Last 3 months", "Last 6 months", "This year"])
        
        if period == "Last 30 days":
            days = 30
        elif period == "Last 3 months":
            days = 90
        elif period == "Last 6 months":
            days = 180
        else:
            days = 365
        
        category_df = get_category_spending(user_id, days)
        if not category_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(category_df, values='total', names='category', 
                           title=f"Spending by Category ({period})")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(category_df, x='category', y='total',
                           title=f"Category Spending ({period})")
                fig.update_layout(xaxis_title='Category', yaxis_title='Amount (₹)')
                st.plotly_chart(fig, use_container_width=True)
            
            # Category table
            category_df['total'] = category_df['total'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(category_df, use_container_width=True)
        else:
            st.info("No data available for the selected period.")

def main():
    """Main application function"""
    # Initialize database
    init_db()
    
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    # Authentication
    if st.session_state.user is None:
        st.title("💰 Expense Tracker")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.subheader("Login to your account")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login", type="primary")
                
                if login_btn:
                    if username and password:
                        user_id = authenticate_user(username, password)
                        if user_id:
                            st.session_state.user = username
                            st.session_state.user_id = user_id
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please enter both username and password")
        
        with tab2:
            st.subheader("Create a new account")
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                register_btn = st.form_submit_button("Register", type="primary")
                
                if register_btn:
                    if new_username and new_password and confirm_password:
                        if new_password == confirm_password:
                            if create_user(new_username, new_password):
                                st.success("Account created successfully! Please login.")
                            else:
                                st.error("Username already exists")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill all fields")
    
    else:
        # Main application
        st.title(f"💰 Expense Tracker - Welcome, {st.session_state.user}!")
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            page = st.selectbox("Go to", 
                              ["Dashboard", "Add Expense", "Expense List", "Reports"])
            
            st.markdown("---")
            if st.button("🚪 Logout", type="secondary"):
                st.session_state.user = None
                st.session_state.user_id = None
                st.rerun()
        
        # Page routing
        user_id = st.session_state.user_id
        
        if page == "Dashboard":
            render_dashboard(user_id)
        elif page == "Add Expense":
            render_add_expense(user_id)
        elif page == "Expense List":
            render_expense_list(user_id)
        elif page == "Reports":
            render_reports(user_id)

if __name__ == "__main__":
    main()
