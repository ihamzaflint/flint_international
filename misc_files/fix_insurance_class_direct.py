#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
import logging
import os
import argparse
from getpass import getpass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger(__name__)

def run_fix(dbname, user, password=None, host='localhost', port=5432):
    """Fix invalid insurance_class values directly in the database"""
    _logger.info(f"Connecting to database {dbname} to fix insurance class values")
    
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = False
        cr = conn.cursor()
        
        # Get the ID of class B for mapping
        cr.execute("SELECT id FROM insurance_class WHERE code = 'B' LIMIT 1")
        result = cr.fetchone()
        
        if not result:
            _logger.warning("Cannot find insurance class with code 'B'. Using default fallback.")
            # Get default class as fallback
            cr.execute("SELECT id FROM insurance_class ORDER BY sequence, id LIMIT 1")
            result = cr.fetchone()
            
        if not result:
            _logger.error("Cannot find any insurance class to map 'b' values. Aborting fix.")
            return False
            
        b_class_id = result[0]
        _logger.info(f"Found insurance class B with ID: {b_class_id}")
        
        # Check what tables and columns exist
        tables_to_check = [
            ('logistic_order', ['insurance_class', 'insurance_class_from', 'insurance_class_to']),
            ('logistic_order_line', ['insurance_class']),
            # Add other tables if needed
        ]
        
        for table, columns in tables_to_check:
            # Check if table exists
            cr.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
            if not cr.fetchone()[0]:
                _logger.info(f"Table {table} does not exist, skipping.")
                continue
                
            for column in columns:
                # Check if column exists
                cr.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}'
                """)
                result = cr.fetchone()
                
                if not result:
                    _logger.info(f"Column {column} does not exist in {table}, skipping.")
                    continue
                    
                column_name, data_type = result
                
                if data_type == 'character varying':
                    # It's still a string column - check for 'b' values
                    cr.execute(f"""
                        SELECT COUNT(*)
                        FROM {table}
                        WHERE {column} = 'b'
                    """)
                    count = cr.fetchone()[0]
                    
                    if count > 0:
                        _logger.info(f"Found {count} records with lowercase 'b' in {table}.{column}")
                        # Update with correct B class ID
                        cr.execute(f"""
                            UPDATE {table}
                            SET {column} = %s::text
                            WHERE {column} = 'b'
                        """, (str(b_class_id),))
                        _logger.info(f"Updated {cr.rowcount} records in {table}.{column}")
                
                elif data_type == 'integer':
                    # It's already an integer column - we shouldn't have issues here
                    _logger.info(f"Column {table}.{column} is already integer type, checking for invalid data")
                    
                    # Check for any non-numeric values that might be causing issues
                    try:
                        cr.execute(f"""
                            SELECT id, {column}
                            FROM {table}
                            WHERE {column}::text ~ '[^0-9]'
                        """)
                        bad_rows = cr.fetchall()
                        
                        if bad_rows:
                            _logger.warning(f"Found {len(bad_rows)} records with non-integer values in {table}.{column}")
                            for row_id, bad_value in bad_rows:
                                _logger.info(f"Record {row_id} has value '{bad_value}'")
                                cr.execute(f"""
                                    UPDATE {table}
                                    SET {column} = %s
                                    WHERE id = %s
                                """, (b_class_id, row_id))
                    except Exception as e:
                        _logger.error(f"Error checking {table}.{column}: {e}")
        
        # Check for temporary columns that might still have 'b' values
        temp_columns = [
            ('logistic_order', ['insurance_class_temp', 'insurance_class_from_temp', 'insurance_class_to_temp']),
            ('logistic_order_line', ['insurance_class_temp']),
        ]
        
        for table, temp_cols in temp_columns:
            # Check if table exists
            cr.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
            if not cr.fetchone()[0]:
                continue
                
            for column in temp_cols:
                # Check if column exists
                cr.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}'
                """)
                result = cr.fetchone()
                
                if not result:
                    continue
                    
                column_name, data_type = result
                
                if data_type == 'integer':
                    # It's already integer, but we should check for any NULL values
                    # where original column had a value - these might be unmapped 'b' values
                    original_col = column.replace('_temp', '')
                    cr.execute(f"""
                        SELECT EXISTS(SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = '{original_col}')
                    """)
                    
                    if cr.fetchone()[0]:  # Original column exists
                        cr.execute(f"""
                            UPDATE {table}
                            SET {column} = %s
                            WHERE {original_col} = 'b' AND ({column} IS NULL OR {column}::text = 'b')
                        """, (b_class_id,))
                        if cr.rowcount > 0:
                            _logger.info(f"Updated {cr.rowcount} records in {table}.{column} with missing mappings for 'b'")
        
        # Look for any columns that might be in the process of being converted
        # This is where Odoo might be failing - it's trying to convert a column with 'b' values
        cr.execute("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE data_type = 'character varying' 
            AND table_name LIKE 'logistic_%' 
            AND column_name LIKE 'insurance_class%'
        """)
        
        for table, column in cr.fetchall():
            _logger.info(f"Checking potentially problematic column: {table}.{column}")
            
            cr.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE {column} = 'b'
            """)
            count = cr.fetchone()[0]
            
            if count > 0:
                _logger.info(f"Found {count} records with lowercase 'b' in {table}.{column}")
                # Update with correct B class ID as string (since column is string type)
                cr.execute(f"""
                    UPDATE {table}
                    SET {column} = %s::text
                    WHERE {column} = 'b'
                """, (str(b_class_id),))
                _logger.info(f"Updated {cr.rowcount} records in {table}.{column}")
        
        conn.commit()
        _logger.info("Database updates committed successfully")
        return True
        
    except Exception as e:
        _logger.error(f"Error fixing insurance class values: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'cr' in locals() and cr:
            cr.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix insurance class values in database')
    parser.add_argument('-d', '--database', required=True, help='Database name')
    parser.add_argument('-u', '--user', default=os.getenv('PGUSER', 'odoo'), help='Database user')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='Database host')
    parser.add_argument('-p', '--port', default=os.getenv('PGPORT', 5432), type=int, help='Database port')
    parser.add_argument('--password', help='Database password (will prompt if not provided)')
    
    args = parser.parse_args()
    
    if args.password is None:
        args.password = os.getenv('PGPASSWORD') or getpass('Database password: ')
    
    if run_fix(args.database, args.user, args.password, args.host, args.port):
        print("Fix completed successfully!")
    else:
        print("Fix failed. Check the logs for details.")
