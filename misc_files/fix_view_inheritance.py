#!/usr/bin/env python3
import sys
import psycopg2
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def fix_view_inheritance(conn):
    """Find and fix issues with view inheritance that could cause recursive issues."""
    with conn.cursor() as cur:
        try:
            # 1. First, identify views with broken inheritance (inherits from non-existent views)
            cur.execute("""
                SELECT v.id, v.name, v.inherit_id, p.name as parent_name
                FROM ir_ui_view v
                LEFT JOIN ir_ui_view p ON v.inherit_id = p.id
                WHERE v.inherit_id IS NOT NULL 
                AND p.id IS NULL
                AND v.model LIKE 'security.%'
            """)
            broken_inheritance = cur.fetchall()
            
            if broken_inheritance:
                logger.info(f"Found {len(broken_inheritance)} views with broken inheritance")
                for view_id, name, inherit_id, parent_name in broken_inheritance:
                    logger.info(f"Removing inherit_id for view: {name} (ID: {view_id})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET inherit_id = NULL 
                        WHERE id = %s
                    """, (view_id,))
            else:
                logger.info("No views with broken inheritance found")

            # 2. Check for circular inheritance
            cur.execute("""
                WITH RECURSIVE inheritance_chain AS (
                    SELECT id, name, inherit_id, ARRAY[id] as path, false as cycle
                    FROM ir_ui_view
                    WHERE model LIKE 'security.%'
                    AND inherit_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT v.id, v.name, v.inherit_id, 
                           ic.path || v.id, 
                           v.id = ANY(ic.path)
                    FROM ir_ui_view v
                    JOIN inheritance_chain ic ON v.inherit_id = ic.id
                    WHERE NOT ic.cycle
                )
                SELECT id, name, inherit_id, path
                FROM inheritance_chain
                WHERE cycle = true
            """)
            circular_inheritance = cur.fetchall()
            
            if circular_inheritance:
                logger.info(f"Found {len(circular_inheritance)} views involved in circular inheritance")
                for view_id, name, inherit_id, path in circular_inheritance:
                    logger.info(f"Breaking circular inheritance for view: {name} (ID: {view_id})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET inherit_id = NULL 
                        WHERE id = %s
                    """, (view_id,))
            else:
                logger.info("No views with circular inheritance found")

            # 3. Find views that might be causing deep recursion
            cur.execute("""
                WITH RECURSIVE inheritance_depth AS (
                    SELECT id, name, inherit_id, 1 as depth
                    FROM ir_ui_view
                    WHERE model LIKE 'security.%'
                    AND inherit_id IS NOT NULL
                    
                    UNION ALL
                    
                    SELECT v.id, v.name, v.inherit_id, id.depth + 1
                    FROM ir_ui_view v
                    JOIN inheritance_depth id ON v.inherit_id = id.id
                    WHERE id.depth < 50
                )
                SELECT id, name, inherit_id, depth
                FROM inheritance_depth
                WHERE depth >= 10
                ORDER BY depth DESC
            """)
            deep_inheritance = cur.fetchall()
            
            if deep_inheritance:
                logger.info(f"Found {len(deep_inheritance)} views with deep inheritance chains (10+ levels)")
                for view_id, name, inherit_id, depth in deep_inheritance:
                    logger.info(f"View with deep inheritance: {name} (ID: {view_id}, Depth: {depth})")
                    # Here we just log without modifying, but you could decide to break these as well
            else:
                logger.info("No views with deep inheritance chains found")

            # 4. Check for views with potentially problematic arch values
            cur.execute("""
                SELECT id, name, model
                FROM ir_ui_view
                WHERE model LIKE 'security.%'
                AND inherit_id IS NOT NULL
                AND (
                    arch IS NULL
                    OR arch = ''
                    OR (arch IS NOT NULL AND pg_column_size(arch) = 0)
                )
            """)
            problematic_inherited_views = cur.fetchall()
            
            if problematic_inherited_views:
                logger.info(f"Found {len(problematic_inherited_views)} inherited views with problematic arch values")
                for view_id, name, model in problematic_inherited_views:
                    logger.info(f"Setting minimal valid arch for problematic view: {name} (ID: {view_id})")
                    cur.execute("""
                        UPDATE ir_ui_view 
                        SET arch = '<?xml version="1.0"?><data></data>' 
                        WHERE id = %s
                    """, (view_id,))
            else:
                logger.info("No inherited views with problematic arch values found")
            
            # 5. Check for views involved in the traceback error (500 error)
            cur.execute("""
                SELECT id, name, model, inherit_id
                FROM ir_ui_view
                WHERE model = 'ir.ui.view'
                AND name LIKE '%exception%'
            """)
            exception_views = cur.fetchall()
            
            if exception_views:
                logger.info(f"Found {len(exception_views)} exception template views")
                for view_id, name, model, inherit_id in exception_views:
                    logger.info(f"Exception view: {name} (ID: {view_id}, Inherit ID: {inherit_id})")
            else:
                logger.info("No exception template views found")

            conn.commit()
            logger.info("View inheritance fixes applied successfully")
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Error fixing view inheritance: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 fix_view_inheritance.py <dbname> <user> <password> [host] [port]")
        sys.exit(1)
    
    dbname = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    host = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    port = sys.argv[5] if len(sys.argv) > 5 else 5432
    
    conn = connect_to_db(dbname, user, password, host, port)
    try:
        fix_view_inheritance(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
