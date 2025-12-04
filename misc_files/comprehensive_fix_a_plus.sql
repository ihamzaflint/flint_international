-- Comprehensive fix for "a_plus" values in the database
-- This script will find and fix any "a_plus" values that might cause integer conversion errors

-- First, let's find all tables and columns that might contain "a_plus"
DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
BEGIN
    RAISE NOTICE 'Starting comprehensive search for "a_plus" values...';
    
    -- Loop through all tables
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        RAISE NOTICE 'Checking table: %', table_record.table_name;
        
        -- Loop through all varchar/text columns in this table
        FOR column_record IN 
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = table_record.table_name
            AND data_type IN ('character varying', 'text', 'varchar')
        LOOP
            -- Check if this column contains "a_plus"
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I ILIKE %L', 
                               table_record.table_name, column_record.column_name, '%a_plus%');
            EXECUTE query_text INTO result_count;
            
            IF result_count > 0 THEN
                RAISE NOTICE 'Found % records with "a_plus" in %.% - FIXING...', 
                           result_count, table_record.table_name, column_record.column_name;
                
                -- Set all "a_plus" values to NULL
                query_text := format('UPDATE %I SET %I = NULL WHERE %I ILIKE %L', 
                                   table_record.table_name, column_record.column_name, 
                                   column_record.column_name, '%a_plus%');
                EXECUTE query_text;
                
                RAISE NOTICE 'Fixed % records in %.%', result_count, table_record.table_name, column_record.column_name;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Comprehensive "a_plus" cleanup completed.';
END $$;

-- Also fix any other non-integer values in columns that should be integers
-- This is a more targeted approach for known problematic columns
DO $$
DECLARE
    column_info RECORD;
    query_text TEXT;
    result_count INTEGER;
BEGIN
    RAISE NOTICE 'Checking for non-integer values in columns that should be integers...';
    
    -- List of columns that should be integers (foreign keys)
    FOR column_info IN 
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND column_name IN ('insurance_policy_id', 'insurance_class', 'insurance_class_id')
        AND data_type IN ('character varying', 'text', 'varchar')
    LOOP
        RAISE NOTICE 'Checking % in table %', column_info.column_name, column_info.table_name;
        
        -- Find non-integer values
        query_text := format('SELECT COUNT(*) FROM %I WHERE %I IS NOT NULL AND %I != %L AND %I !~ %L', 
                           column_info.table_name, column_info.column_name, column_info.column_name, 
                           '', column_info.column_name, '^[0-9]+$');
        EXECUTE query_text INTO result_count;
        
        IF result_count > 0 THEN
            RAISE NOTICE 'Found % non-integer values in %.% - FIXING...', 
                       result_count, column_info.table_name, column_info.column_name;
            
            -- Set non-integer values to NULL
            query_text := format('UPDATE %I SET %I = NULL WHERE %I IS NOT NULL AND %I != %L AND %I !~ %L', 
                               column_info.table_name, column_info.column_name, column_info.column_name,
                               column_info.column_name, '', column_info.column_name, '^[0-9]+$');
            EXECUTE query_text;
            
            RAISE NOTICE 'Fixed % records in %.%', result_count, column_info.table_name, column_info.column_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Non-integer value cleanup completed.';
END $$;

-- Verify the fix worked
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- If the above query returns no rows, the fix was successful 