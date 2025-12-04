# -*- coding: utf-8 -*-
import logging
from odoo import fields
from odoo.tools import sql

_logger = logging.getLogger(__name__)

# Store original methods for patching
original_convert_column = sql._convert_column

def patched_convert_column(cr, tablename, columnname, columntype, using=None):
    """Patch for sql._convert_column that handles invalid insurance class values"""
    _logger.info(f"PATCH: Converting column {tablename}.{columnname} to {columntype}")
    
    # Check if this is an insurance class field being converted to integer
    is_insurance_field = (
        columnname in ['insurance_class', 'insurance_class_from', 'insurance_class_to'] or
        columnname.endswith('_temp')
    )
    
    if is_insurance_field and columntype.startswith('int'):
        try:
            # Get mapping of all insurance classes to fix non-integer values
            _logger.info(f"PATCH: Getting insurance class mapping for {tablename}.{columnname}")
            
            # Build complete mapping of codes to IDs
            cr.execute("SELECT id, code FROM insurance_class WHERE code IS NOT NULL")
            class_mapping = {row[1]: row[0] for row in cr.fetchall()}
            
            # Also add lowercase and variant mappings
            variant_mapping = {}
            for code, class_id in class_mapping.items():
                # Add lowercase variant
                variant_mapping[code.lower()] = class_id
                
                # Add underscore variants for special cases
                if '+' in code:
                    underscore_variant = code.replace('+', '_plus')
                    variant_mapping[underscore_variant] = class_id
                    variant_mapping[underscore_variant.lower()] = class_id
                
                # Add no-plus variants
                if '+' in code:
                    no_plus_variant = code.replace('+', '')
                    variant_mapping[no_plus_variant] = class_id
                    variant_mapping[no_plus_variant.lower()] = class_id
            
            # Merge all mappings
            all_mappings = {**class_mapping, **variant_mapping}
            _logger.info(f"PATCH: Using insurance class mappings: {all_mappings}")
            
            # Fix special case for "a_plus"
            if 'A+' in class_mapping:
                try:
                    a_plus_id = class_mapping['A+']
                    cr.execute(f"""
                        UPDATE {tablename}
                        SET {columnname} = %s::text
                        WHERE {columnname} = 'a_plus'
                    """, (str(a_plus_id),))
                    fixed_count = cr.rowcount
                    if fixed_count:
                        _logger.info(f"PATCH: Fixed {fixed_count} records with 'a_plus' in {tablename}.{columnname}")
                except Exception as e:
                    _logger.error(f"PATCH: Error fixing 'a_plus' values: {e}")
            
            # Fix general case for all invalid codes
            for code_variant, class_id in all_mappings.items():
                # Skip if the code variant is a number already
                if code_variant.isdigit():
                    continue
                    
                try:
                    cr.execute(f"""
                        UPDATE {tablename}
                        SET {columnname} = %s::text
                        WHERE {columnname} = %s
                    """, (str(class_id), code_variant))
                    fixed_count = cr.rowcount
                    if fixed_count:
                        _logger.info(f"PATCH: Fixed {fixed_count} records with '{code_variant}' in {tablename}.{columnname}")
                except Exception as e:
                    _logger.error(f"PATCH: Error fixing '{code_variant}' values: {e}")
                    
        except Exception as e:
            _logger.error(f"PATCH: Error in pre-conversion patch: {e}")
    
    # Call the original method to perform the actual conversion
    return original_convert_column(cr, tablename, columnname, columntype, using)

# Apply the patch
_logger.info("APPLYING PATCH: Replacing sql._convert_column with patched version")
sql._convert_column = patched_convert_column
