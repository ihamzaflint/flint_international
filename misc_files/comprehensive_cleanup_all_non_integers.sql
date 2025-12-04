-- Comprehensive cleanup for ALL non-integer values in the database
-- This script will find and fix any non-integer values that might cause conversion errors

-- First, let's find ALL non-integer values in any column that should be integer
DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
    result_value TEXT;
BEGIN
    RAISE NOTICE 'Starting comprehensive search for ALL non-integer values...';
    
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
            -- Check if this column contains any non-integer values
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I IS NOT NULL AND %I != %L AND %I !~ %L', 
                               table_record.table_name, column_record.column_name, column_record.column_name, 
                               '', column_record.column_name, '^[0-9]+$');
            EXECUTE query_text INTO result_count;
            
            IF result_count > 0 THEN
                RAISE NOTICE 'Found % non-integer values in %.% - FIXING...', 
                           result_count, table_record.table_name, column_record.column_name;
                
                -- Show some examples of the non-integer values
                query_text := format('SELECT %I FROM %I WHERE %I IS NOT NULL AND %I != %L AND %I !~ %L LIMIT 5', 
                                   column_record.column_name, table_record.table_name, column_record.column_name,
                                   column_record.column_name, '', column_record.column_name, '^[0-9]+$');
                EXECUTE query_text;
                
                -- Set all non-integer values to NULL
                query_text := format('UPDATE %I SET %I = NULL WHERE %I IS NOT NULL AND %I != %L AND %I !~ %L', 
                                   table_record.table_name, column_record.column_name, column_record.column_name,
                                   column_record.column_name, '', column_record.column_name, '^[0-9]+$');
                EXECUTE query_text;
                
                RAISE NOTICE 'Fixed % records in %.%', result_count, table_record.table_name, column_record.column_name;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Comprehensive non-integer cleanup completed.';
END $$;

-- Also specifically check for any single character values that might be problematic
DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
BEGIN
    RAISE NOTICE 'Checking for single character values that might cause issues...';
    
    -- Loop through all tables
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        -- Loop through all varchar/text columns in this table
        FOR column_record IN 
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = table_record.table_name
            AND data_type IN ('character varying', 'text', 'varchar')
        LOOP
            -- Check for single character values (like 'a', 'b', etc.)
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I IS NOT NULL AND length(%I) = 1 AND %I !~ %L', 
                               table_record.table_name, column_record.column_name, column_record.column_name,
                               column_record.column_name, '^[0-9]$');
            EXECUTE query_text INTO result_count;
            
            IF result_count > 0 THEN
                RAISE NOTICE 'Found % single character values in %.% - FIXING...', 
                           result_count, table_record.table_name, column_record.column_name;
                
                -- Show the single character values
                query_text := format('SELECT %I FROM %I WHERE %I IS NOT NULL AND length(%I) = 1 AND %I !~ %L LIMIT 10', 
                                   column_record.column_name, table_record.table_name, column_record.column_name,
                                   column_record.column_name, column_record.column_name, '^[0-9]$');
                EXECUTE query_text;
                
                -- Set single character values to NULL
                query_text := format('UPDATE %I SET %I = NULL WHERE %I IS NOT NULL AND length(%I) = 1 AND %I !~ %L', 
                                   table_record.table_name, column_record.column_name, column_record.column_name,
                                   column_record.column_name, column_record.column_name, '^[0-9]$');
                EXECUTE query_text;
                
                RAISE NOTICE 'Fixed % single character records in %.%', result_count, table_record.table_name, column_record.column_name;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Single character value cleanup completed.';
END $$;

-- Verify the fix worked by checking for any remaining non-integer values
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_from' as column_name, id, insurance_class_from::text as value
FROM logistic_order 
WHERE insurance_class_from IS NOT NULL AND insurance_class_from::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_to' as column_name, id, insurance_class_to::text as value
FROM logistic_order 
WHERE insurance_class_to IS NOT NULL AND insurance_class_to::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_from_id' as column_name, id, insurance_class_from_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_from_id IS NOT NULL AND insurance_class_from_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_to_id' as column_name, id, insurance_class_to_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_to_id IS NOT NULL AND insurance_class_to_id::text !~ '^[0-9]+$';

-- If the above query returns no rows, the fix was successful 