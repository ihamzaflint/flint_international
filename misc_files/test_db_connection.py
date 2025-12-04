#!/usr/bin/env python3
"""
Database connection test script.
This script tests the database connection and identifies potential issues.
"""

import sys
import os
import psycopg2
from psycopg2 import OperationalError, InterfaceError

def find_odoo_path():
    """Find Odoo installation path automatically"""
    possible_paths = [
        '/opt/odoo',
        '/usr/lib/odoo',
        '/usr/local/odoo',
        os.path.expanduser('~/odoo'),
        os.path.expanduser('~/odoo17-server'),
        '/var/lib/odoo',
    ]
    
    try:
        import odoo
        return os.path.dirname(os.path.dirname(odoo.__file__))
    except ImportError:
        pass
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'odoo-bin')):
            return path
    
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if 'odoo-bin' in files:
            return root
    
    return None

# Find and add Odoo path
odoo_path = find_odoo_path()
if odoo_path:
    sys.path.insert(0, odoo_path)
    print(f"Found Odoo at: {odoo_path}")
else:
    print("Warning: Could not find Odoo installation. Trying to import anyway...")

try:
    import odoo
    from odoo import api, fields, models
    from odoo.exceptions import AccessError
except ImportError as e:
    print(f"Error importing Odoo: {e}")
    print("Please ensure Odoo is properly installed and accessible.")
    sys.exit(1)

def test_database_connection():
    """Test database connection and identify issues"""
    
    try:
        print("Testing database connection...")
        
        # Initialize Odoo
        odoo.cli.server.main()
        
        # Get the environment
        env = api.Environment.manage()
        
        print("✓ Database connection successful")
        
        # Test basic queries
        print("Testing basic queries...")
        
        # Test 1: Simple select
        try:
            env.cr.execute("SELECT 1")
            result = env.cr.fetchone()
            print("✓ Simple query test passed")
        except Exception as e:
            print(f"✗ Simple query test failed: {e}")
            return False
        
        # Test 2: Check ir.model.access table
        try:
            env.cr.execute("SELECT COUNT(*) FROM ir_model_access")
            count = env.cr.fetchone()[0]
            print(f"✓ ir_model_access table accessible ({count} records)")
        except Exception as e:
            print(f"✗ ir_model_access table test failed: {e}")
            return False
        
        # Test 3: Check res_groups table
        try:
            env.cr.execute("SELECT COUNT(*) FROM res_groups")
            count = env.cr.fetchone()[0]
            print(f"✓ res_groups table accessible ({count} records)")
        except Exception as e:
            print(f"✗ res_groups table test failed: {e}")
            return False
        
        # Test 4: Check for problematic access rights
        try:
            env.cr.execute("""
                SELECT COUNT(*) 
                FROM ir_model_access ima
                LEFT JOIN res_groups rg ON ima.group_id = rg.id
                WHERE ima.group_id IS NOT NULL 
                AND rg.id IS NULL
            """)
            count = env.cr.fetchone()[0]
            if count > 0:
                print(f"⚠ Found {count} problematic access rights (referencing non-existent groups)")
            else:
                print("✓ No problematic access rights found")
        except Exception as e:
            print(f"✗ Access rights check failed: {e}")
            return False
        
        # Test 5: Check module status
        try:
            module = env['ir.module.module'].search([('name', '=', 'scs_operation')])
            if module:
                print(f"✓ scs_operation module found (state: {module.state})")
            else:
                print("⚠ scs_operation module not found")
        except Exception as e:
            print(f"✗ Module check failed: {e}")
            return False
        
        # Test 6: Check cursor state
        try:
            if env.cr.closed:
                print("✗ Cursor is closed")
                return False
            else:
                print("✓ Cursor is open and active")
        except Exception as e:
            print(f"✗ Cursor state check failed: {e}")
            return False
        
        print("\n✓ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            env.cr.close()
        except:
            pass

def diagnose_connection_issues():
    """Diagnose common connection issues"""
    
    print("\n=== Connection Diagnosis ===")
    
    # Check if we can get database configuration
    try:
        import odoo.tools.config as config
        print(f"Database host: {config['db_host']}")
        print(f"Database port: {config['db_port']}")
        print(f"Database name: {config['db_name']}")
        print(f"Database user: {config['db_user']}")
    except Exception as e:
        print(f"Could not read database configuration: {e}")
    
    # Test direct PostgreSQL connection
    try:
        import odoo.tools.config as config
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            database=config['db_name'],
            user=config['db_user'],
            password=config['db_password']
        )
        print("✓ Direct PostgreSQL connection successful")
        conn.close()
    except Exception as e:
        print(f"✗ Direct PostgreSQL connection failed: {e}")
    
    # Check for common issues
    print("\n=== Common Issues Check ===")
    
    # Check if database is accessible
    try:
        import odoo.tools.config as config
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            database=config['db_name'],
            user=config['db_user'],
            password=config['db_password']
        )
        cursor = conn.cursor()
        
        # Check for long-running transactions
        cursor.execute("""
            SELECT pid, state, query_start, query 
            FROM pg_stat_activity 
            WHERE state = 'active' 
            AND query NOT LIKE '%pg_stat_activity%'
        """)
        long_running = cursor.fetchall()
        if long_running:
            print(f"⚠ Found {len(long_running)} long-running transactions")
            for pid, state, query_start, query in long_running:
                print(f"  PID {pid}: {state} since {query_start}")
        else:
            print("✓ No long-running transactions found")
        
        # Check for locks
        cursor.execute("""
            SELECT locktype, database, relation::regclass, mode, granted
            FROM pg_locks l
            JOIN pg_database d ON l.database = d.oid
            WHERE d.datname = current_database()
        """)
        locks = cursor.fetchall()
        if locks:
            print(f"⚠ Found {len(locks)} database locks")
        else:
            print("✓ No database locks found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database diagnostics failed: {e}")

if __name__ == "__main__":
    print("=== Database Connection Test ===")
    
    if test_database_connection():
        print("\n✓ Database connection is healthy")
    else:
        print("\n✗ Database connection has issues")
        diagnose_connection_issues() 