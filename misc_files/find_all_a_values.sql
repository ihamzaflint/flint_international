-- Find ALL "a" values in the database that might be causing conversion errors
-- This will help us identify where the "a" value is coming from

DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
    result_value TEXT;
BEGIN
    RAISE NOTICE 'Searching for ALL "a" values in the database...';
    
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
            -- Check if this column contains exactly "a"
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I = %L', 
                               table_record.table_name, column_record.column_name, 'a');
            EXECUTE query_text INTO result_count;
            
            IF result_count > 0 THEN
                RAISE NOTICE 'Found % records with "a" in %.%', 
                           result_count, table_record.table_name, column_record.column_name;
                
                -- Show the actual values
                query_text := format('SELECT id, %I FROM %I WHERE %I = %L LIMIT 5', 
                                   column_record.column_name, table_record.table_name, 
                                   column_record.column_name, 'a');
                EXECUTE query_text;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Search for "a" values completed.';
END $$;

-- Also check for any values that start with "a" in insurance-related columns
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text LIKE 'a%'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text LIKE 'a%'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text LIKE 'a%'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_from_id' as column_name, id, insurance_class_from_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_from_id IS NOT NULL AND insurance_class_from_id::text LIKE 'a%'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_to_id' as column_name, id, insurance_class_to_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_to_id IS NOT NULL AND insurance_class_to_id::text LIKE 'a%'; 