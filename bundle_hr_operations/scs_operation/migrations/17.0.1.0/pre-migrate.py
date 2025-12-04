# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, installed_version):
    # Make sure the insurance_class table exists
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'insurance_class')")
    table_exists = cr.fetchone()[0]
    
    if not table_exists:
        _logger.error("insurance_class table does not exist. Cannot proceed with migration.")
        return
    
    # First, check if the insurance_class model has records
    cr.execute("SELECT COUNT(*) FROM insurance_class")
    count = cr.fetchone()[0]
    if count == 0:
        _logger.warning("No insurance.class records found. Creating default records.")
        # Create default insurance classes to map all possible codes
        cr.execute("""
            INSERT INTO insurance_class (name, code, sequence, create_uid, create_date, write_uid, write_date, active)
            VALUES 
            ('A Class', 'A', 10, 1, now(), 1, now(), true),
            ('A+ Class', 'A+', 20, 1, now(), 1, now(), true),
            ('B Class', 'B', 30, 1, now(), 1, now(), true),
            ('B+ Class', 'B+', 40, 1, now(), 1, now(), true),
            ('C Class', 'C', 50, 1, now(), 1, now(), true),
            ('C+ Class', 'C+', 60, 1, now(), 1, now(), true),
            ('Default', 'default', 100, 1, now(), 1, now(), true)
            RETURNING id
        """)
        
    # Get the default class id for fallback
    cr.execute("SELECT id FROM insurance_class WHERE code = 'default' LIMIT 1")
    result = cr.fetchone()
    if not result:
        cr.execute("SELECT id FROM insurance_class ORDER BY sequence, id LIMIT 1")
        result = cr.fetchone()
    default_class_id = result[0]
    
    _logger.info(f"Using default insurance class ID: {default_class_id}")
    
    # Log unique insurance class values before migration for debugging
    cr.execute("SELECT DISTINCT insurance_class FROM logistic_order WHERE insurance_class IS NOT NULL")
    classes = [row[0] for row in cr.fetchall()]
    _logger.info(f"Found insurance classes in logistic_order: {classes}")
    
    cr.execute("SELECT DISTINCT insurance_class FROM logistic_order_line WHERE insurance_class IS NOT NULL")
    line_classes = [row[0] for row in cr.fetchall()]
    _logger.info(f"Found insurance classes in logistic_order_line: {line_classes}")
    
    # Create mapping between string codes and IDs to fix case sensitivity and variations
    class_mapping = {}
    cr.execute("SELECT id, code FROM insurance_class")
    for class_id, code in cr.fetchall():
        if code:
            class_mapping[code.upper()] = class_id
    
    _logger.info(f"Insurance class mapping: {class_mapping}")
    
    # ---- logistic_order migration ----
    # First check if the temporary columns already exist
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'logistic_order' AND column_name = 'insurance_class_temp')")
    temp_exists = cr.fetchone()[0]
    
    if not temp_exists:
        cr.execute("""
            ALTER TABLE logistic_order
            ADD COLUMN insurance_class_temp INTEGER,
            ADD COLUMN insurance_class_from_temp INTEGER,
            ADD COLUMN insurance_class_to_temp INTEGER;
        """)

    # Map old string codes to insurance.class ids for logistic_order
    # Using UPPER() to handle case sensitivity issues
    cr.execute("""
        UPDATE logistic_order lo
        SET insurance_class_temp = ic.id
        FROM insurance_class ic
        WHERE UPPER(lo.insurance_class) = UPPER(ic.code);
    """)
    
    # Set default class for unmapped values
    cr.execute("""
        UPDATE logistic_order
        SET insurance_class_temp = %s
        WHERE insurance_class IS NOT NULL 
        AND insurance_class_temp IS NULL
    """, (default_class_id,))
    
    # Log migration results
    cr.execute("SELECT COUNT(*) FROM logistic_order WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL")
    unmapped_count = cr.fetchone()[0]
    if unmapped_count > 0:
        _logger.warning(f"{unmapped_count} logistic_order records still have unmapped insurance_class values")
        
        # Manually fix any unmapped values by direct update
        cr.execute("SELECT id, insurance_class FROM logistic_order WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL")
        for record_id, class_code in cr.fetchall():
            if class_code:
                # Try to find a matching class code ignoring case
                matched_id = None
                if class_code.upper() in class_mapping:
                    matched_id = class_mapping[class_code.upper()]
                else:
                    _logger.warning(f"No match found for '{class_code}', using default")
                    matched_id = default_class_id
                
                cr.execute("""
                    UPDATE logistic_order 
                    SET insurance_class_temp = %s
                    WHERE id = %s
                """, (matched_id, record_id))

    # Do the same for insurance_class_from
    cr.execute("""
        UPDATE logistic_order lo
        SET insurance_class_from_temp = ic.id
        FROM insurance_class ic
        WHERE UPPER(lo.insurance_class_from) = UPPER(ic.code);
    """)
    
    cr.execute("""
        UPDATE logistic_order
        SET insurance_class_from_temp = %s
        WHERE insurance_class_from IS NOT NULL 
        AND insurance_class_from_temp IS NULL
    """, (default_class_id,))
    
    # Manual fix for any remaining unmapped values
    cr.execute("SELECT id, insurance_class_from FROM logistic_order WHERE insurance_class_from IS NOT NULL AND insurance_class_from_temp IS NULL")
    for record_id, class_code in cr.fetchall():
        if class_code:
            matched_id = None
            if class_code.upper() in class_mapping:
                matched_id = class_mapping[class_code.upper()]
            else:
                matched_id = default_class_id
            
            cr.execute("""
                UPDATE logistic_order 
                SET insurance_class_from_temp = %s
                WHERE id = %s
            """, (matched_id, record_id))

    # Do the same for insurance_class_to
    cr.execute("""
        UPDATE logistic_order lo
        SET insurance_class_to_temp = ic.id
        FROM insurance_class ic
        WHERE UPPER(lo.insurance_class_to) = UPPER(ic.code);
    """)
    
    cr.execute("""
        UPDATE logistic_order
        SET insurance_class_to_temp = %s
        WHERE insurance_class_to IS NOT NULL 
        AND insurance_class_to_temp IS NULL
    """, (default_class_id,))
    
    # Manual fix for any remaining unmapped values
    cr.execute("SELECT id, insurance_class_to FROM logistic_order WHERE insurance_class_to IS NOT NULL AND insurance_class_to_temp IS NULL")
    for record_id, class_code in cr.fetchall():
        if class_code:
            matched_id = None
            if class_code.upper() in class_mapping:
                matched_id = class_mapping[class_code.upper()]
            else:
                matched_id = default_class_id
            
            cr.execute("""
                UPDATE logistic_order 
                SET insurance_class_to_temp = %s
                WHERE id = %s
            """, (matched_id, record_id))
            
    # Make sure all temp columns have valid values before dropping original columns
    cr.execute("UPDATE logistic_order SET insurance_class_temp = %s WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL", (default_class_id,))
    cr.execute("UPDATE logistic_order SET insurance_class_from_temp = %s WHERE insurance_class_from IS NOT NULL AND insurance_class_from_temp IS NULL", (default_class_id,))
    cr.execute("UPDATE logistic_order SET insurance_class_to_temp = %s WHERE insurance_class_to IS NOT NULL AND insurance_class_to_temp IS NULL", (default_class_id,))

    # Drop the old columns - with column existence check
    cr.execute("ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_class")
    cr.execute("ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_class_from")
    cr.execute("ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_class_to")

    # Rename the temporary columns
    cr.execute("ALTER TABLE logistic_order RENAME COLUMN insurance_class_temp TO insurance_class")
    cr.execute("ALTER TABLE logistic_order RENAME COLUMN insurance_class_from_temp TO insurance_class_from")
    cr.execute("ALTER TABLE logistic_order RENAME COLUMN insurance_class_to_temp TO insurance_class_to")

    # ---- logistic_order_line migration ----
    # First check if the temporary column already exists
    cr.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'logistic_order_line' AND column_name = 'insurance_class_temp')")
    temp_exists = cr.fetchone()[0]
    
    if not temp_exists:
        cr.execute("""
            ALTER TABLE logistic_order_line
            ADD COLUMN insurance_class_temp INTEGER;
        """)

    cr.execute("""
        UPDATE logistic_order_line lol
        SET insurance_class_temp = ic.id
        FROM insurance_class ic
        WHERE UPPER(lol.insurance_class) = UPPER(ic.code);
    """)
    
    # Set default class for unmapped values
    cr.execute("""
        UPDATE logistic_order_line
        SET insurance_class_temp = %s
        WHERE insurance_class IS NOT NULL 
        AND insurance_class_temp IS NULL
    """, (default_class_id,))
    
    # Log migration results
    cr.execute("SELECT COUNT(*) FROM logistic_order_line WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL")
    unmapped_count = cr.fetchone()[0]
    if unmapped_count > 0:
        _logger.warning(f"{unmapped_count} logistic_order_line records still have unmapped insurance_class values")
        
        # Manually fix any unmapped values by direct update
        cr.execute("SELECT id, insurance_class FROM logistic_order_line WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL")
        for record_id, class_code in cr.fetchall():
            if class_code:
                # Try to find a matching class code ignoring case
                matched_id = None
                if class_code.upper() in class_mapping:
                    matched_id = class_mapping[class_code.upper()]
                else:
                    _logger.warning(f"No match found for '{class_code}' in order line, using default")
                    matched_id = default_class_id
                
                cr.execute("""
                    UPDATE logistic_order_line 
                    SET insurance_class_temp = %s
                    WHERE id = %s
                """, (matched_id, record_id))
    
    # Make sure all temp columns have valid values before dropping original columns
    cr.execute("UPDATE logistic_order_line SET insurance_class_temp = %s WHERE insurance_class IS NOT NULL AND insurance_class_temp IS NULL", (default_class_id,))

    # Drop the old columns - with column existence check
    cr.execute("ALTER TABLE logistic_order_line DROP COLUMN IF EXISTS insurance_class")
    
    # Rename the temporary column
    cr.execute("ALTER TABLE logistic_order_line RENAME COLUMN insurance_class_temp TO insurance_class")
    
    # Log completion
    _logger.info("Migration of insurance class fields completed successfully")
    
    _logger.info("Migration of insurance class fields completed successfully")

