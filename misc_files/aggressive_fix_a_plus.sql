-- Aggressive fix for "a_plus" values in ANY table and column
-- This script will search all tables and fix any "a_plus" values found

DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    query_text TEXT;
    result_count INTEGER;
    update_query TEXT;
BEGIN
    RAISE NOTICE 'Starting aggressive search and fix for "a_plus" values...';
    
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
            -- Check if this column contains "a_plus"
            query_text := format('SELECT COUNT(*) FROM %I WHERE %I ILIKE %L', 
                               table_record.table_name, 
                               column_record.column_name, 
                               '%a_plus%');
            
            BEGIN
                EXECUTE query_text INTO result_count;
                IF result_count > 0 THEN
                    RAISE NOTICE 'Found % records with "a_plus" in %.% - FIXING...', 
                                result_count, table_record.table_name, column_record.column_name;
                    
                    -- Update the values to NULL
                    update_query := format('UPDATE %I SET %I = NULL WHERE %I ILIKE %L', 
                                         table_record.table_name,
                                         column_record.column_name,
                                         column_record.column_name,
                                         '%a_plus%');
                    
                    EXECUTE update_query;
                    RAISE NOTICE 'Fixed % records in %.%', result_count, table_record.table_name, column_record.column_name;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing %.%: %', table_record.table_name, column_record.column_name, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Aggressive fix completed!';
END $$;

-- Also fix any non-integer values in specific columns that are being converted to Many2one
-- Logistic Order
UPDATE logistic_order 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE logistic_order 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE logistic_order 
SET insurance_partner_id = NULL 
WHERE insurance_partner_id IS NOT NULL AND insurance_partner_id::text !~ '^[0-9]+$';

-- Employee Insurance Line
UPDATE employee_insurance_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET policy_id = NULL 
WHERE policy_id IS NOT NULL AND policy_id::text !~ '^[0-9]+$';

-- Logistic Order Line
UPDATE logistic_order_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE logistic_order_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

-- Helpdesk Ticket
UPDATE helpdesk_ticket 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE helpdesk_ticket 
SET insurance_class_id = NULL 
WHERE insurance_class_id IS NOT NULL AND insurance_class_id::text !~ '^[0-9]+$';

-- Drop the insurance_policy column if it exists
ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_policy;

-- Also check for any other potential Many2one fields that might have string values
-- This is a more comprehensive approach
DO $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    update_query TEXT;
BEGIN
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'logistic_order', 'logistic_order_line', 'employee_insurance_line', 
            'helpdesk_ticket', 'insurance_policy', 'insurance_class',
            'hr_employee', 'hr_employee_family'
        )
    LOOP
        FOR column_record IN 
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = table_record.table_name
            AND data_type IN ('character varying', 'text', 'varchar')
            AND column_name LIKE '%_id'  -- Focus on columns that look like foreign keys
        LOOP
            BEGIN
                update_query := format('UPDATE %I SET %I = NULL WHERE %I IS NOT NULL AND %I::text !~ %L', 
                                     table_record.table_name,
                                     column_record.column_name,
                                     column_record.column_name,
                                     column_record.column_name,
                                     '^[0-9]+$');
                
                EXECUTE update_query;
                RAISE NOTICE 'Cleaned non-integer values in %.%', table_record.table_name, column_record.column_name;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error cleaning %.%: %', table_record.table_name, column_record.column_name, SQLERRM;
            END;
        END LOOP;
    END LOOP;
END $$; 