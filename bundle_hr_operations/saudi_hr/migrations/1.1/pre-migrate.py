# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Migration script to migrate visa_no data to identification_id field
    for all existing HR employee records.
    """
    # Update all employees where visa_no is not null/empty and identification_id is null/empty
    cr.execute("""
        UPDATE hr_employee 
        SET identification_id = visa_no 
        WHERE visa_no IS NOT NULL 
        AND visa_no != '' 
        AND (identification_id IS NULL OR identification_id = '')
    """)
    
    # Get the number of rows affected by the update
    updated_count = cr.rowcount
    
    # Log the migration result
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Migration completed: {updated_count} employee records migrated from visa_no to identification_id")
