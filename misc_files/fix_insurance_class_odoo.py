# This script fixes lowercase 'b' values in insurance_class fields
# Run with: ./odoo-bin shell -d DATABASE_NAME < fix_insurance_class_odoo.py

import logging
import odoo
from odoo.api import Environment

_logger = logging.getLogger(__name__)

def fix_lowercase_b_values(env):
    """Fix lowercase 'b' values in insurance_class fields"""
    _logger.info("Running emergency fix for lowercase 'b' values in insurance class fields")
    
    # Check if tables exist
    env.cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'logistic_order')")
    if not env.cr.fetchone()[0]:
        _logger.error("logistic_order table doesn't exist, skipping fix")
        return False

    env.cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'insurance_class')")
    if not env.cr.fetchone()[0]:
        _logger.error("insurance_class table doesn't exist, skipping fix")
        return False
    
    # Get the ID of class B for mapping
    env.cr.execute("SELECT id FROM insurance_class WHERE code = 'B' LIMIT 1")
    result = env.cr.fetchone()
    if not result:
        _logger.error("Cannot find insurance class with code 'B'. Using default fallback.")
        # Get default class as fallback
        env.cr.execute("SELECT id FROM insurance_class WHERE code = 'default' LIMIT 1")
        result = env.cr.fetchone()
        if not result:
            env.cr.execute("SELECT id FROM insurance_class ORDER BY sequence, id LIMIT 1")
            result = env.cr.fetchone()
    
    if not result:
        _logger.error("Cannot find any insurance class to map 'b' values. Aborting fix.")
        return False
        
    b_class_id = result[0]
    _logger.info(f"Found insurance class B with ID: {b_class_id}")
    
    # Check for lowercase 'b' values
    env.cr.execute("""
        SELECT COUNT(*) FROM logistic_order 
        WHERE insurance_class = 'b' OR insurance_class_from = 'b' OR insurance_class_to = 'b'
    """)
    count = env.cr.fetchone()[0]
    _logger.info(f"Found {count} records with lowercase 'b' in logistic_order")
    
    env.cr.execute("""
        SELECT COUNT(*) FROM logistic_order_line 
        WHERE insurance_class = 'b'
    """)
    line_count = env.cr.fetchone()[0]
    _logger.info(f"Found {line_count} records with lowercase 'b' in logistic_order_line")
    
    # Check if we're dealing with temp columns or final columns
    env.cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'logistic_order' AND column_name = 'insurance_class_temp')")
    using_temp_columns = env.cr.fetchone()[0]
    
    if using_temp_columns:
        # We're in the middle of migration, fix temp columns
        _logger.info("Fixing lowercase 'b' values in temporary columns")
        
        # Fix logistic_order insurance_class_temp
        env.cr.execute("""
            UPDATE logistic_order
            SET insurance_class_temp = %s
            WHERE insurance_class = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class_temp")
        
        # Fix logistic_order insurance_class_from_temp
        env.cr.execute("""
            UPDATE logistic_order
            SET insurance_class_from_temp = %s
            WHERE insurance_class_from = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class_from_temp")
        
        # Fix logistic_order insurance_class_to_temp
        env.cr.execute("""
            UPDATE logistic_order
            SET insurance_class_to_temp = %s
            WHERE insurance_class_to = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class_to_temp")
        
        # Fix logistic_order_line insurance_class_temp
        env.cr.execute("""
            UPDATE logistic_order_line
            SET insurance_class_temp = %s
            WHERE insurance_class = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in logistic_order_line.insurance_class_temp")
        
    else:
        # Direct conversion already happened, let's look for raw 'b' values in final columns
        _logger.info("Fixing any remaining lowercase 'b' values in final columns")
        
        # Check if the columns are string or integer type
        env.cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'logistic_order' AND column_name = 'insurance_class'")
        data_type = env.cr.fetchone()
        
        if data_type and data_type[0] == 'character varying':
            # Still string type, convert 'b' to the proper ID
            _logger.info("Columns are still string type, fixing 'b' values")
            
            # Fix logistic_order fields
            env.cr.execute("""
                UPDATE logistic_order
                SET insurance_class = %s::text
                WHERE insurance_class = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class")
            
            env.cr.execute("""
                UPDATE logistic_order
                SET insurance_class_from = %s::text
                WHERE insurance_class_from = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class_from")
            
            env.cr.execute("""
                UPDATE logistic_order
                SET insurance_class_to = %s::text
                WHERE insurance_class_to = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {env.cr.rowcount} records in logistic_order.insurance_class_to")
            
            # Fix logistic_order_line
            env.cr.execute("""
                UPDATE logistic_order_line
                SET insurance_class = %s::text
                WHERE insurance_class = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {env.cr.rowcount} records in logistic_order_line.insurance_class")
        else:
            _logger.info("Columns are already integer type, no need to fix 'b' values")

    # Directly fix in any additional temp columns that might exist
    env.cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'insurance_policy' AND column_name = 'insurance_class_from_temp')")
    if env.cr.fetchone()[0]:
        env.cr.execute("""
            UPDATE insurance_policy
            SET insurance_class_from_temp = %s
            WHERE insurance_class_from = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in insurance_policy.insurance_class_from_temp")
    
    env.cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'insurance_policy' AND column_name = 'insurance_class_to_temp')")
    if env.cr.fetchone()[0]:
        env.cr.execute("""
            UPDATE insurance_policy
            SET insurance_class_to_temp = %s
            WHERE insurance_class_to = 'b'
        """, (b_class_id,))
        _logger.info(f"Updated {env.cr.rowcount} records in insurance_policy.insurance_class_to_temp")
    
    # Final catch-all fixes for any string columns that might still have 'b' values
    env.cr.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns 
        WHERE data_type = 'character varying' 
        AND table_name IN ('logistic_order', 'logistic_order_line', 'insurance_policy')
        AND column_name LIKE '%insurance_class%'
    """)
    
    for table, column in env.cr.fetchall():
        env.cr.execute(f"""
            SELECT COUNT(*) FROM {table} 
            WHERE {column} = 'b'
        """)
        count = env.cr.fetchone()[0]
        if count > 0:
            _logger.info(f"Found {count} records with 'b' in {table}.{column}, fixing...")
            env.cr.execute(f"""
                UPDATE {table}
                SET {column} = %s::text
                WHERE {column} = 'b'
            """, (b_class_id,))
            _logger.info(f"Updated {env.cr.rowcount} records in {table}.{column}")
    
    _logger.info("Lowercase 'b' fix completed successfully!")
    return True

# Get the environment - this is necessary when running in script mode
# odoo.registry and odoo.api.Environment will be populated by the shell
from odoo.api import Environment

registry = odoo.registry(odoo.tools.config['db_name'])
with registry.cursor() as cr:
    env = Environment(cr, odoo.SUPERUSER_ID, {})
    
    # Execute the fix
    result = fix_lowercase_b_values(env)
    print(f"Fix executed with result: {result}")

    # Explicitly commit the changes
    cr.commit()
    print("Changes committed to database")
