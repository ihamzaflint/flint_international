#!/usr/bin/env python3
import sys
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default values
DEFAULT_ARCH = '<?xml version="1.0"?><data></data>'

def connect_to_db(dbname, user, password, host='localhost', port=5432):
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        logger.info(f"Connected to database: {dbname}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)

def fix_invalid_view_arch(conn):
    """Find and fix any views with invalid (non-string) arch fields."""
    with conn.cursor() as cur:
        try:
            # First, check for views with NULL arch
            cur.execute("""
                SELECT id, name, model 
                FROM ir_ui_view 
                WHERE arch IS NULL 
                AND model LIKE 'security.%'
            """)
            null_arch_views = cur.fetchall()
            
            if null_arch_views:
                logger.info(f"Found {len(null_arch_views)} views with NULL arch")
                for view_id, name, model in null_arch_views:
                    logger.info(f"Setting default arch for view: {name} (ID: {view_id}, Model: {model})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET arch = %s 
                        WHERE id = %s
                    """, (DEFAULT_ARCH, view_id))
            else:
                logger.info("No views with NULL arch found")

            # Next, check for views with empty string arch
            cur.execute("""
                SELECT id, name, model 
                FROM ir_ui_view 
                WHERE arch = '' 
                AND model LIKE 'security.%'
            """)
            empty_arch_views = cur.fetchall()
            
            if empty_arch_views:
                logger.info(f"Found {len(empty_arch_views)} views with empty arch")
                for view_id, name, model in empty_arch_views:
                    logger.info(f"Setting default arch for view: {name} (ID: {view_id}, Model: {model})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET arch = %s 
                        WHERE id = %s
                    """, (DEFAULT_ARCH, view_id))
            else:
                logger.info("No views with empty arch found")
                
            # Identify views with non-text values in arch (this is more complex)
            # We'll look for views where trying to access arch as a string fails
            cur.execute("""
                SELECT id, name, model 
                FROM ir_ui_view 
                WHERE model LIKE 'security.%'
                AND (
                    (arch IS NOT NULL AND pg_column_size(arch) = 0)
                    OR 
                    (arch IS NOT NULL AND octet_length(arch::text) = 0)
                )
            """)
            invalid_arch_views = cur.fetchall()
            
            if invalid_arch_views:
                logger.info(f"Found {len(invalid_arch_views)} views with potentially invalid arch")
                for view_id, name, model in invalid_arch_views:
                    logger.info(f"Setting default arch for view with potentially invalid value: {name} (ID: {view_id}, Model: {model})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET arch = %s 
                        WHERE id = %s
                    """, (DEFAULT_ARCH, view_id))
            else:
                logger.info("No views with potentially invalid arch found")
                
            # Check for duplicate views (same model and priority)
            cur.execute("""
                SELECT model, priority, COUNT(*) 
                FROM ir_ui_view 
                WHERE model LIKE 'security.%'
                GROUP BY model, priority 
                HAVING COUNT(*) > 1
            """)
            duplicate_views = cur.fetchall()
            
            if duplicate_views:
                logger.info(f"Found {len(duplicate_views)} sets of duplicate views (same model and priority)")
                for model, priority, count in duplicate_views:
                    logger.info(f"Duplicate views: {count} views for model {model} with priority {priority}")
            else:
                logger.info("No duplicate views found")
                
            conn.commit()
            logger.info("Fixes applied successfully")
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Error fixing views: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 fix_security_views.py <dbname> <user> <password> [host] [port]")
        sys.exit(1)
    
    dbname = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    host = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    port = sys.argv[5] if len(sys.argv) > 5 else 5432
    
    conn = connect_to_db(dbname, user, password, host, port)
    try:
        fix_invalid_view_arch(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
