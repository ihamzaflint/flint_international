-- Emergency fix for "a_plus" conversion error
-- This script addresses the most likely causes of the conversion error

-- 1. First, let's check if there are any field definitions with "a_plus" in domains or defaults
UPDATE ir_model_fields 
SET domain = NULL 
WHERE domain ILIKE '%a_plus%';

UPDATE ir_model_fields 
SET default_value = NULL 
WHERE default_value ILIKE '%a_plus%';

-- 2. Check for any configuration parameters containing "a_plus"
UPDATE ir_config_parameter 
SET value = NULL 
WHERE value ILIKE '%a_plus%';

-- 3. Check for any view definitions containing "a_plus"
UPDATE ir_ui_view 
SET arch = REPLACE(arch, 'a_plus', '') 
WHERE arch ILIKE '%a_plus%';

-- 4. Check for any data in ir_model_data that might contain "a_plus"
UPDATE ir_model_data 
SET res_id = NULL 
WHERE res_id::text ILIKE '%a_plus%';

-- 5. Fix any remaining "a_plus" values in the main tables
-- Logistic Order
UPDATE logistic_order 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE logistic_order 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

UPDATE logistic_order 
SET insurance_partner_id = NULL 
WHERE insurance_partner_id IS NOT NULL AND insurance_partner_id::text ILIKE '%a_plus%';

-- Employee Insurance Line
UPDATE employee_insurance_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE employee_insurance_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

UPDATE employee_insurance_line 
SET policy_id = NULL 
WHERE policy_id IS NOT NULL AND policy_id::text ILIKE '%a_plus%';

-- Logistic Order Line
UPDATE logistic_order_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE logistic_order_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- Helpdesk Ticket
UPDATE helpdesk_ticket 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE helpdesk_ticket 
SET insurance_class_id = NULL 
WHERE insurance_class_id IS NOT NULL AND insurance_class_id::text ILIKE '%a_plus%';

-- 6. Also fix any non-integer values in these columns
UPDATE logistic_order 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE logistic_order 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE logistic_order_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE logistic_order_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

-- 7. Drop the insurance_policy column if it exists
ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_policy;

-- 8. Check for any other potential issues - look for any column that might be converted to integer
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
            'helpdesk_ticket', 'insurance_policy', 'insurance_class'
        )
    LOOP
        FOR column_record IN 
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = table_record.table_name
            AND data_type IN ('character varying', 'text', 'varchar')
            AND (
                column_name LIKE '%_id' 
                OR column_name LIKE '%insurance%' 
                OR column_name LIKE '%policy%' 
                OR column_name LIKE '%class%'
            )
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