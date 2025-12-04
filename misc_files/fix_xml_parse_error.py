#!/usr/bin/env python3
import sys
import psycopg2
import logging
import base64
import json
import re

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

def fix_xml_parse_errors(conn):
    """Fix issues with view arch values that cause XML parsing errors."""
    with conn.cursor() as cur:
        try:
            # 1. First look for views related to error handling and templates
            # The traceback involves an error in ir_http._handle_error -> _get_values_500_error -> View._views_get
            cur.execute("""
                SELECT id, name, model, inherit_id, mode, active
                FROM ir_ui_view
                WHERE (name LIKE '%error%' OR name LIKE '%exception%')
                AND (model = 'ir.http' OR model = 'ir.ui.view')
            """)
            error_views = cur.fetchall()
            
            if error_views:
                logger.info(f"Found {len(error_views)} views related to error handling")
                for view_id, name, model, inherit_id, mode, active in error_views:
                    logger.info(f"Error view: {name} (ID: {view_id}, Model: {model}, Active: {active})")
                    
                    # Check if view arch is retrievable as text
                    try:
                        cur.execute("SELECT arch FROM ir_ui_view WHERE id = %s", (view_id,))
                        arch = cur.fetchone()[0]
                        
                        # If we can get it, check if it's a valid XML string
                        if not isinstance(arch, str) or not arch.strip():
                            logger.warning(f"View {name} (ID: {view_id}) has invalid arch value")
                            # Set a valid default arch
                            cur.execute("""
                                UPDATE ir_ui_view 
                                SET arch = '<?xml version="1.0"?><data></data>' 
                                WHERE id = %s
                            """, (view_id,))
                            logger.info(f"Fixed arch for view {name} (ID: {view_id})")
                    except Exception as e:
                        logger.error(f"Error checking arch for view {name} (ID: {view_id}): {e}")
                        # Try to fix it even if we couldn't retrieve it
                        cur.execute("""
                            UPDATE ir_ui_view 
                            SET arch = '<?xml version="1.0"?><data></data>' 
                            WHERE id = %s
                        """, (view_id,))
                        logger.info(f"Set default arch for view {name} (ID: {view_id}) after error")
            else:
                logger.info("No error-related views found")

            # 2. Look for views in the security_management module
            cur.execute("""
                SELECT id, name, model, inherit_id, active
                FROM ir_ui_view
                WHERE (model LIKE 'security.%' OR name LIKE 'security%')
                AND id IN (
                    SELECT res_id FROM ir_model_data 
                    WHERE model = 'ir.ui.view' 
                    AND module = 'security_management'
                )
            """)
            security_views = cur.fetchall()
            
            if security_views:
                logger.info(f"Found {len(security_views)} views in security_management module")
                for view_id, name, model, inherit_id, active in security_views:
                    logger.info(f"Security view: {name} (ID: {view_id}, Model: {model}, Active: {active})")
                    
                    # Check if view arch is retrievable as text
                    try:
                        cur.execute("SELECT arch FROM ir_ui_view WHERE id = %s", (view_id,))
                        arch = cur.fetchone()[0]
                        
                        # If we can get it, check if it's a valid XML string
                        if not isinstance(arch, str) or not arch.strip():
                            logger.warning(f"View {name} (ID: {view_id}) has invalid arch value")
                            # Set a valid default arch
                            cur.execute("""
                                UPDATE ir_ui_view 
                                SET arch = '<?xml version="1.0"?><data></data>' 
                                WHERE id = %s
                            """, (view_id,))
                            logger.info(f"Fixed arch for view {name} (ID: {view_id})")
                    except Exception as e:
                        logger.error(f"Error checking arch for view {name} (ID: {view_id}): {e}")
                        # Try to fix it even if we couldn't retrieve it
                        cur.execute("""
                            UPDATE ir_ui_view 
                            SET arch = '<?xml version="1.0"?><data></data>' 
                            WHERE id = %s
                        """, (view_id,))
                        logger.info(f"Set default arch for view {name} (ID: {view_id}) after error")
            else:
                logger.info("No security_management views found")

            # 3. Force all applicable views to have string arch fields
            # Use JSONB_TYPEOF to check if arch is stored as a non-string type
            # This requires PostgreSQL 9.4+
            cur.execute("""
                UPDATE ir_ui_view 
                SET arch = '<?xml version="1.0"?><data></data>'
                WHERE (
                    arch IS NULL
                    OR arch = ''
                    OR (arch IS NOT NULL AND (
                        pg_typeof(arch) != 'text'::regtype
                        OR octet_length(arch::text) = 0
                    ))
                )
                AND (
                    model LIKE 'security.%'
                    OR id IN (
                        SELECT res_id FROM ir_model_data 
                        WHERE model = 'ir.ui.view' 
                        AND module = 'security_management'
                    )
                )
                RETURNING id, name, model
            """)
            
            fixed_views = cur.fetchall()
            if fixed_views:
                logger.info(f"Fixed {len(fixed_views)} views with non-string arch values")
                for view_id, name, model in fixed_views:
                    logger.info(f"Fixed view: {name} (ID: {view_id}, Model: {model})")
            else:
                logger.info("No views with non-string arch values found")

            conn.commit()
            logger.info("XML parse error fixes applied successfully")
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Error fixing XML parse errors: {e}")
            sys.exit(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 fix_xml_parse_error.py <dbname> <user> <password> [host] [port]")
        sys.exit(1)
    
    dbname = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    host = sys.argv[4] if len(sys.argv) > 4 else 'localhost'
    port = sys.argv[5] if len(sys.argv) > 5 else 5432
    
    conn = connect_to_db(dbname, user, password, host, port)
    try:
        fix_xml_parse_errors(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
