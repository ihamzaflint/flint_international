#!/usr/bin/env python3
# IMPORTANT: Run this script in Odoo.sh by:
# 1. Navigate to your Odoo.sh shell
# 2. Execute: python3 odoo_shell_fix.py

import logging
import sys
import os

# Add required code to access the Odoo environment
import odoo
from odoo.tools import config
from odoo.modules.registry import Registry
from odoo.api import Environment

_logger = logging.getLogger(__name__)

def fix_lowercase_b_values(cr):
    """Fix lowercase 'b' values in insurance_class fields"""
    _logger.info("Running emergency fix for lowercase 'b' values in insurance class fields")
    
    # Check if tables exist
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'logistic_order')")
    if not cr.fetchone()[0]:
        _logger.error("logistic_order table doesn't exist, skipping fix")
        return False

    cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'insurance_class')")
    if not cr.fetchone()[0]:
        _logger.error("insurance_class table doesn't exist, skipping fix")
        return False
    
    # Get the ID of class B for mapping
    cr.execute("SELECT id FROM insurance_class WHERE code = 'B' LIMIT 1")
    result = cr.fetchone()
    if not result:
        _logger.error("Cannot find insurance class with code 'B'. Using default fallback.")
        # Get default class as fallback
        cr.execute("SELECT id FROM insurance_class WHERE code = 'default' LIMIT 1")
        result = cr.fetchone()
        if not result:
            cr.execute("SELECT id FROM insurance_class ORDER BY sequence, id LIMIT 1")
            result = cr.fetchone()
    
    if not result:
        _logger.error("Cannot find any insurance class to map 'b' values. Aborting fix.")
        return False
        
    b_class_id = result[0]
    _logger.info(f"Found insurance class B with ID: {b_class_id}")
    
    # Check for lowercase 'b' values
    cr.execute("""
        SELECT COUNT(*) FROM logistic_order 
        WHERE insurance_class = 'b' OR insurance_class_from = 'b' OR insurance_class_to = 'b'
    """)
    count = cr.fetchone()[0]
    _logger.info(f"Found {count} records with lowercase 'b' in logistic_order")
    
    cr.execute("""
        SELECT COUNT(*) FROM logistic_order_line 
        WHERE insurance_class = 'b'
    """)
    line_count = cr.fetchone()[0]
    _logger.info(f"Found {line_count} records with lowercase 'b' in logistic_order_line")
    
    # Check if we're dealing with temp columns or final columns
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'logistic_order' AND column_name = 'insurance_class_temp')")
    using_temp_columns = cr.fetchone()[0]
    
    if using_temp_columns:
        # We're in the middle of migration, fix temp columns
        _logger.info("Fixing lowercase 'b' values in temporary columns")
        
        # Fix logistic_order insurance_class_temp
        cr.execute("""
            UPDATE logistic_order
            SET insurance_class_temp = %s
            WHERE insurance_class = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class_temp")
        
        # Fix logistic_order insurance_class_from_temp
        cr.execute("""
            UPDATE logistic_order
            SET insurance_class_from_temp = %s
            WHERE insurance_class_from = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class_from_temp")
        
        # Fix logistic_order insurance_class_to_temp
        cr.execute("""
            UPDATE logistic_order
            SET insurance_class_to_temp = %s
            WHERE insurance_class_to = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class_to_temp")
        
        # Fix logistic_order_line insurance_class_temp
        cr.execute("""
            UPDATE logistic_order_line
            SET insurance_class_temp = %s
            WHERE insurance_class = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in logistic_order_line.insurance_class_temp")
        
    else:
        # Direct conversion already happened, let's look for raw 'b' values in final columns
        _logger.info("Fixing any remaining lowercase 'b' values in final columns")
        
        # Check if the columns are string or integer type
        cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'logistic_order' AND column_name = 'insurance_class'")
        data_type = cr.fetchone()
        
        if data_type and data_type[0] == 'character varying':
            # Still string type, convert 'b' to the proper ID
            _logger.info("Columns are still string type, fixing 'b' values")
            
            # Fix logistic_order fields
            cr.execute("""
                UPDATE logistic_order
                SET insurance_class = %s::text
                WHERE insurance_class = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class")
            
            cr.execute("""
                UPDATE logistic_order
                SET insurance_class_from = %s::text
                WHERE insurance_class_from = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class_from")
            
            cr.execute("""
                UPDATE logistic_order
                SET insurance_class_to = %s::text
                WHERE insurance_class_to = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {cr.rowcount} records in logistic_order.insurance_class_to")
            
            # Fix logistic_order_line
            cr.execute("""
                UPDATE logistic_order_line
                SET insurance_class = %s::text
                WHERE insurance_class = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {cr.rowcount} records in logistic_order_line.insurance_class")
        else:
            _logger.info("Columns are already integer type, no need to fix 'b' values")

    # Directly fix in any additional temp columns that might exist
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'insurance_policy' AND column_name = 'insurance_class_from_temp')")
    if cr.fetchone()[0]:
        cr.execute("""
            UPDATE insurance_policy
            SET insurance_class_from_temp = %s
            WHERE insurance_class_from = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in insurance_policy.insurance_class_from_temp")
    
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'insurance_policy' AND column_name = 'insurance_class_to_temp')")
    if cr.fetchone()[0]:
        cr.execute("""
            UPDATE insurance_policy
            SET insurance_class_to_temp = %s
            WHERE insurance_class_to = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {cr.rowcount} records in insurance_policy.insurance_class_to_temp")
    
    # Final catch-all fixes for any string columns that might still have 'b' values
    cr.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns 
        WHERE data_type = 'character varying' 
        AND table_name IN ('logistic_order', 'logistic_order_line', 'insurance_policy')
        AND column_name LIKE '%insurance_class%'
    """)
    
    for table, column in cr.fetchall():
        cr.execute(f"""
            SELECT COUNT(*) FROM {table} 
            WHERE {column} = 'b'
        """)
        count = cr.fetchone()[0]
        if count > 0:
            _logger.info(f"Found {count} records with 'b' in {table}.{column}, fixing...")
            cr.execute(f"""
                UPDATE {table}
                SET {column} = %s::text
                WHERE {column} = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {cr.rowcount} records in {table}.{column}")
    
    _logger.info("Lowercase 'b' fix completed successfully!")
    return True

def main():
    # Set up logging for both console and file
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    
    # Get the database name from the environment or command line
    db_name = os.environ.get('DB_NAME', None)
    
    # If no db_name from environment, check command line arguments
    if not db_name and len(sys.argv) > 1:
        db_name = sys.argv[1]
    
    # If still no db_name, try to get it from Odoo config
    if not db_name:
        db_name = config.get('db_name')
    
    if not db_name:
        print("ERROR: No database name specified.")
        print("Usage: python3 odoo_shell_fix.py [database_name]")
        print("   or: Set the DB_NAME environment variable")
        sys.exit(1)
    
    print(f"Starting fix for database: {db_name}")
    
    # Initialize the Odoo registry and environment
    try:
        registry = Registry(db_name)
        with registry.cursor() as cr:
            print("Connected to database. Running fix...")
            result = fix_lowercase_b_values(cr)
            if result:
                print("Fix completed successfully!")
                print("Committing changes...")
                cr.commit()
                print("Changes committed to database.")
            else:
                print("Fix failed or wasn't necessary.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("Script completed.")

if __name__ == "__main__":
    main()
