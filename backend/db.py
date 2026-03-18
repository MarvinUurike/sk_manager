import json
import traceback
import os
import decimal
from datetime import datetime
from typing import Dict, Any, List, Optional
import pg8000.dbapi
from aws_utils import get_table

# Table environment variables
EQUIPMENT_TABLE = 'EQUIPMENT_TABLE'
LENDING_TABLE = 'LENDING_TABLE'
PHOTOS_BUCKET = os.environ.get('PHOTOS_BUCKET')

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection() -> Optional[pg8000.dbapi.Connection]:
    """Create a new database connection with error handling"""
    # Keep diagnostics for now until we prove it works
    import socket, sys
    print(f"DIAGNOSTIC: Attempting to resolve {DB_HOST}...")
    sys.stdout.flush()
    try:
        ip = socket.gethostbyname(DB_HOST)
        print(f"DIAGNOSTIC: Resolved {DB_HOST} to {ip}")
    except Exception as dns_e:
        print(f"DIAGNOSTIC: DNS RESOLUTION FAILED for {DB_HOST}: {dns_e}")

    # NAT check
    try:
        print("DIAGNOSTIC: Checking NAT/External access to 8.8.8.8:53...")
        sys.stdout.flush()
        s = socket.create_connection(("8.8.8.8", 53), timeout=1)
        print("DIAGNOSTIC: External access SUCCESSFUL")
        s.close()
    except Exception as nat_e:
        print(f"DIAGNOSTIC: External access FAILED: {nat_e}")

    sys.stdout.flush()

    try:
        # We don't use a global connection here to avoid leak issues in Lambda reuse
        conn = pg8000.dbapi.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=int(DB_PORT),
            timeout=5
        )
        return conn
    except Exception as e:
        print(f"pg8000 connect FAILED: {e}")
        sys.stdout.flush()
        return None

def init_db_schema():
    """Run once to ensure tables exist in RDS"""
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # Table tracking all changes to equipment
            cur.execute("""
                CREATE TABLE IF NOT EXISTS equipment_history (
                    id SERIAL PRIMARY KEY,
                    equipment_id VARCHAR(50) NOT NULL,
                    action_type VARCHAR(20) NOT NULL,
                    name VARCHAR(255),
                    quantity INT,
                    location VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table tracking all lendings and returns
            cur.execute("""
                CREATE TABLE IF NOT EXISTS lending_history (
                    id SERIAL PRIMARY KEY,
                    lending_id VARCHAR(50) NOT NULL,
                    equipment_id VARCHAR(50) NOT NULL,
                    borrower VARCHAR(255) NOT NULL,
                    quantity INT NOT NULL,
                    action_type VARCHAR(20) NOT NULL, -- LEND, RETURN
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Diagnostic: Check counts
            cur.execute("SELECT COUNT(*) FROM equipment_history")
            eq_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM lending_history")
            lend_count = cur.fetchone()[0]
            print(f"DATABASE DIAGNOSTICS: eq_history={eq_count}, lend_history={lend_count}")
            
            conn.commit()
        except Exception as e:
            print(f"Error initializing schema: {e}")
        finally:
            cur.close()

def log_equipment_history(equipment_id, action_type, data=None):
    """Log an equipment change to RDS"""
    conn = get_db_connection()
    if not conn: return
    
    if data is None: data = {}
    cur = conn.cursor()
    try:
        # Cast quantity to int for DB compatibility
        qty = int(data.get('quantity', 0)) if data.get('quantity') is not None else 0
        cur.execute("""
            INSERT INTO equipment_history (equipment_id, action_type, name, quantity, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            equipment_id, 
            action_type, 
            data.get('name'), 
            qty, 
            data.get('location')
        ))
        conn.commit()
        print(f"Logged equipment history: {action_type} for {equipment_id} (count: {cur.rowcount})")
    except Exception as e:
        print(f"Error logging equipment history: {e}")
    finally:
        cur.close()

def log_lending_history(lending_id, equipment_id, borrower, quantity, action_type):
    """Log a lending action to RDS"""
    conn = get_db_connection()
    if not conn: return
    
    cur = conn.cursor()
    try:
        # Cast quantity to int for DB compatibility
        qty = int(quantity) if quantity is not None else 0
        cur.execute("""
            INSERT INTO lending_history (lending_id, equipment_id, borrower, quantity, action_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (lending_id, equipment_id, borrower, qty, action_type))
        conn.commit()
        print(f"Logged lending history: {action_type} for {equipment_id} (count: {cur.rowcount})")
    except Exception as e:
        print(f"Error logging lending history: {e}")
    finally:
        cur.close()

def get_equipment_history(equipment_id: str) -> List[Dict[str, Any]]:
    """Retrieve combined history from all tables"""
    conn = get_db_connection()
    if not conn: 
        print(f"FAILED TO CONNECT TO DB for history of {equipment_id}")
        return []
    
    cur = conn.cursor()
    try:
        # Get equipment state changes
        cur.execute("""
            SELECT action_type, name, category, quantity, location, timestamp
            FROM equipment_history 
            WHERE equipment_id = %s 
        """, (equipment_id,))
        eq_rows = cur.fetchall()
        
        # Get lending/return history
        cur.execute("""
            SELECT action_type, borrower, quantity, timestamp, 'LENDING' as origin
            FROM lending_history 
            WHERE equipment_id = %s 
        """, (equipment_id,))
        lend_rows = cur.fetchall()
        
        history = []
        # Process equipment rows
        for row in eq_rows:
            history.append({
                "action": row[0],
                "details": f"{row[0]} - {row[1]} (Qty: {row[2]})",
                "timestamp": row[3].isoformat() if row[3] else None,
                "unix": row[3].timestamp() if row[3] else 0
            })
            
        # Process lending rows
        for row in lend_rows:
            verb = "Lent" if row[0] == 'LEND' else "Returned"
            history.append({
                "action": row[0],
                "borrower": row[1],
                "quantity": row[2],
                "details": f"{verb} {row[2]} to/from {row[1]}",
                "timestamp": row[3].isoformat() if row[3] else None,
                "unix": row[3].timestamp() if row[3] else 0
            })
            
        # Sort chronologically (newest first)
        history.sort(key=lambda x: x['unix'], reverse=True)
        print(f"Found {len(history)} history records for {equipment_id}")
        return history
    except Exception as e:
        print(f"Error fetching history: {e}")
        traceback.print_exc()
        return []
    finally:
        cur.close()
