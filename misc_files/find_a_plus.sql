-- Comprehensive search for "a_plus" in ALL tables and columns
-- This will help us identify exactly where the problematic value is stored

-- First, let's find all tables that might contain "a_plus"
DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
BEGIN
    RAISE NOTICE 'Searching for "a_plus" in all tables...';
    
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        RAISE NOTICE 'Checking table: %', table_record.table_name;
        
        FOR column_record IN 
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = table_record.table_name
            AND data_type IN ('character varying', 'text', 'varchar')
        LOOP
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I ILIKE %L', 
                               table_record.table_name, 
                               column_record.column_name, 
                               '%a_plus%');
            
            BEGIN
                EXECUTE query_text INTO result_count;
                IF result_count > 0 THEN
                    RAISE NOTICE 'Found % records with "a_plus" in %.%', 
                                result_count, table_record.table_name, column_record.column_name;
                    
                    -- Show the actual records
                    query_text := format('SELECT id, %I FROM %I WHERE %I ILIKE %L LIMIT 5', 
                                       column_record.column_name,
                                       table_record.table_name, 
                                       column_record.column_name, 
                                       '%a_plus%');
                    RAISE NOTICE 'Query: %', query_text;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error checking %.%: %', table_record.table_name, column_record.column_name, SQLERRM;
            END;
        END LOOP;
    END LOOP;
END $$;

-- Now let's check specific tables that are most likely to have this issue
-- Check logistic_order table
SELECT 'logistic_order' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_partner_id' as column_name, id, insurance_partner_id::text as value
FROM logistic_order 
WHERE insurance_partner_id IS NOT NULL AND insurance_partner_id::text ILIKE '%a_plus%';

-- Check employee_insurance_line table
SELECT 'employee_insurance_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM employee_insurance_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'policy_id' as column_name, id, policy_id::text as value
FROM employee_insurance_line 
WHERE policy_id IS NOT NULL AND policy_id::text ILIKE '%a_plus%';

-- Check logistic_order_line table
SELECT 'logistic_order_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- Check helpdesk_ticket table
SELECT 'helpdesk_ticket' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM helpdesk_ticket 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_id' as column_name, id, insurance_class_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_id IS NOT NULL AND insurance_class_id::text ILIKE '%a_plus%';

-- Check insurance_policy table
SELECT 'insurance_policy' as table_name, 'id' as column_name, id, id::text as value
FROM insurance_policy 
WHERE id::text ILIKE '%a_plus%';

-- Check insurance_class table
SELECT 'insurance_class' as table_name, 'id' as column_name, id, id::text as value
FROM insurance_class 
WHERE id::text ILIKE '%a_plus%';

-- Also check for any other non-integer values in these columns
SELECT 'logistic_order' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM employee_insurance_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'; 