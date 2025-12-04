#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import psycopg2
import logging
import sys

_logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def fix_all_lowercase_b_values(conn_string):
    """Fix all lowercase 'b' values in any table and column related to insurance class"""
    try:
        setup_logging()
        _logger.info("Connecting to database...")
        conn = psycopg2.connect(conn_string)
        cr = conn.cursor()

        # Find all columns in all tables that might contain 'b' as insurance class
        _logger.info("Looking for potential columns with insurance_class...")
        cr.execute("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (column_name LIKE '%insurance_class%' OR column_name LIKE '%class%') 
            AND data_type = 'character varying'
        """)
        
        potential_columns = cr.fetchall()
        _logger.info(f"Found {len(potential_columns)} potential columns to check")
        
        # Get the ID of insurance class B
        cr.execute("SELECT id FROM insurance_class WHERE UPPER(code) = 'B' LIMIT 1")
        result = cr.fetchone()
        if not result:
            _logger.error("Cannot find insurance class with code 'B'. Looking for default class...")
            # Get default class as fallback
            cr.execute("SELECT id FROM insurance_class WHERE code = 'default' LIMIT 1")
            result = cr.fetchone()
            if not result:
                cr.execute("SELECT id FROM insurance_class ORDER BY sequence, id LIMIT 1")
                result = cr.fetchone()
        
        if not result:
            _logger.error("Cannot find any insurance class to map 'b' values. Aborting.")
            return False
            
        b_class_id = result[0]
        _logger.info(f"Using insurance class B with ID: {b_class_id}")
        
        # Check each potential column for 'b' values
        tables_fixed = []
        
        for table_name, column_name in potential_columns:
            # Check if column exists and has 'b' values
            try:
                cr.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table_name}
                    WHERE {column_name} = 'b'
                """)
                count = cr.fetchone()[0]
                
                if count > 0:
                    _logger.info(f"Found {count} rows with 'b' values in {table_name}.{column_name}")
                    
                    # Check if there's a temp column for this field
                    temp_column = f"{column_name}_temp"
                    cr.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name = '{temp_column}'
                        )
                    """)
                    has_temp = cr.fetchone()[0]
                    
                    if has_temp:
                        # Update temp column (used during migration)
                        _logger.info(f"Updating temp column {table_name}.{temp_column}")
                        cr.execute(f"""
                            UPDATE {table_name}
                            SET {temp_column} = %s
                            WHERE {column_name} = 'b'
                        """, (b_class_id,))
                    else:
                        # Check if target column can be directly updated as string 
                        # (sometimes fields are already renamed but not yet converted to integer)
                        _logger.info(f"Updating original column {table_name}.{column_name}")
                        try:
                            cr.execute(f"""
                                UPDATE {table_name}
                                SET {column_name} = %s::text
                                WHERE {column_name} = 'b'
                            """, (str(b_class_id),))
                        except Exception as e:
                            _logger.error(f"Error updating {table_name}.{column_name}: {e}")
                    
                    tables_fixed.append(f"{table_name}.{column_name}")
            except Exception as e:
                _logger.warning(f"Error checking {table_name}.{column_name}: {e}")

        # Check integer columns where 'b' might have been converted incorrectly
        cr.execute("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (column_name LIKE '%insurance_class%' OR column_name LIKE '%class%') 
            AND data_type = 'integer'
        """)
        
        integer_columns = cr.fetchall()
        _logger.info(f"Found {len(integer_columns)} integer columns to check")
        
        # For these columns, we need to check for NULL values where the original column had 'b'
        for table_name, column_name in integer_columns:
            # Only if there's a companion text column
            orig_column = column_name.replace('_temp', '')
            try:
                cr.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{orig_column}'
                        AND data_type = 'character varying'
                    )
                """)
                
                has_orig = cr.fetchone()[0]
                if has_orig:
                    cr.execute(f"""
                        SELECT COUNT(*) 
                        FROM {table_name}
                        WHERE {orig_column} = 'b' AND {column_name} IS NULL
                    """)
                    count = cr.fetchone()[0]
                    
                    if count > 0:
                        _logger.info(f"Found {count} rows with 'b' values and NULL {column_name} in {table_name}")
                        cr.execute(f"""
                            UPDATE {table_name}
                            SET {column_name} = %s
                            WHERE {orig_column} = 'b' AND {column_name} IS NULL
                        """, (b_class_id,))
                        tables_fixed.append(f"{table_name}.{column_name} (NULL)")
            except Exception as e:
                _logger.warning(f"Error checking integer column {table_name}.{column_name}: {e}")

        # Commit the changes
        conn.commit()
        
        if tables_fixed:
            _logger.info(f"Fixed tables/columns: {', '.join(tables_fixed)}")
            _logger.info("All lowercase 'b' values should be fixed now")
            return True
        else:
            _logger.info("No 'b' values found that need fixing")
            return True
    
    except Exception as e:
        _logger.error(f"Error fixing lowercase 'b' values: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix lowercase "b" values in insurance class fields')
    parser.add_argument('--db', required=True, help='Database name')
    parser.add_argument('--user', default='odoo', help='Database user')
    parser.add_argument('--password', default='odoo', help='Database password')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', default='5432', help='Database port')
    
    args = parser.parse_args()
    
    conn_string = f"dbname={args.db} user={args.user} password={args.password} host={args.host} port={args.port}"
    success = fix_all_lowercase_b_values(conn_string)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
