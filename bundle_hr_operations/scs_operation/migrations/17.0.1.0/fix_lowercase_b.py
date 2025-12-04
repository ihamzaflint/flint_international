# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, installed_version):
    """Fix lowercase 'b' values in insurance_class fields before column type conversion"""
    _logger.info("Running emergency fix for lowercase 'b' values in insurance class fields")
    
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
        return
        
    b_class_id = result[0]
    _logger.info(f"Found insurance class B with ID: {b_class_id}")
    
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
        
        # Fix logistic_order insurance_class_from_temp
        cr.execute("""
            UPDATE logistic_order
            SET insurance_class_from_temp = %s
            WHERE insurance_class_from = 'b'
        """, (b_class_id,))
        
        # Fix logistic_order insurance_class_to_temp
        cr.execute("""
            UPDATE logistic_order
            SET insurance_class_to_temp = %s
            WHERE insurance_class_to = 'b'
        """, (b_class_id,))
        
        # Fix logistic_order_line insurance_class_temp
        cr.execute("""
            UPDATE logistic_order_line
            SET insurance_class_temp = %s
            WHERE insurance_class = 'b'
        """, (b_class_id,))
        
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
            
            cr.execute("""
                UPDATE logistic_order
                SET insurance_class_from = %s::text
                WHERE insurance_class_from = 'b'
            """, (b_class_id,))
            
            cr.execute("""
                UPDATE logistic_order
                SET insurance_class_to = %s::text
                WHERE insurance_class_to = 'b'
            """, (b_class_id,))
            
            # Fix logistic_order_line
            cr.execute("""
                UPDATE logistic_order_line
                SET insurance_class = %s::text
                WHERE insurance_class = 'b'
            """, (b_class_id,))
        else:
            _logger.info("Columns are already integer type, no need to fix 'b' values")
    
    # Log completion
    _logger.info("Emergency fix for lowercase 'b' values completed")
