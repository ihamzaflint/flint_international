-- Debug script to identify the exact column causing the "a_plus" conversion error
-- This will help us pinpoint exactly where the issue is occurring

-- First, let's check if there are any columns that are currently varchar/text but should be integer
-- These are the most likely candidates for the conversion error

SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND c.data_type IN ('character varying', 'text', 'varchar')
AND (
    c.column_name LIKE '%insurance%' 
    OR c.column_name LIKE '%policy%' 
    OR c.column_name LIKE '%class%'
    OR c.column_name LIKE '%_id'
)
ORDER BY t.table_name, c.column_name;

-- Now let's check for any "a_plus" values in these specific columns
SELECT 
    'logistic_order' as table_name,
    'insurance_policy_id' as column_name,
    id,
    insurance_policy_id::text as value
FROM logistic_order 
WHERE insurance_policy_id IS NOT NULL 
AND insurance_policy_id::text ILIKE '%a_plus%'

UNION ALL

SELECT 
    'logistic_order' as table_name,
    'insurance_class' as column_name,
    id,
    insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL 
AND insurance_class::text ILIKE '%a_plus%'

UNION ALL

SELECT 
    'employee_insurance_line' as table_name,
    'insurance_policy_id' as column_name,
    id,
    insurance_policy_id::text as value
FROM employee_insurance_line 
WHERE insurance_policy_id IS NOT NULL 
AND insurance_policy_id::text ILIKE '%a_plus%'

UNION ALL

SELECT 
    'employee_insurance_line' as table_name,
    'insurance_class' as column_name,
    id,
    insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL 
AND insurance_class::text ILIKE '%a_plus%'

UNION ALL

SELECT 
    'logistic_order_line' as table_name,
    'insurance_policy_id' as column_name,
    id,
    insurance_policy_id::text as value
FROM logistic_order_line 
WHERE insurance_policy_id IS NOT NULL 
AND insurance_policy_id::text ILIKE '%a_plus%'

UNION ALL

SELECT 
    'logistic_order_line' as table_name,
    'insurance_class' as column_name,
    id,
    insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL 
AND insurance_class::text ILIKE '%a_plus%';

-- Let's also check if there are any system tables or other tables that might contain this value
-- Check ir_model_fields table for any field definitions that might be causing issues
SELECT 
    'ir_model_fields' as table_name,
    'name' as column_name,
    id,
    name as value
FROM ir_model_fields 
WHERE name ILIKE '%a_plus%'

UNION ALL

SELECT 
    'ir_model_fields' as table_name,
    'field_description' as column_name,
    id,
    field_description as value
FROM ir_model_fields 
WHERE field_description ILIKE '%a_plus%';

-- Check if there are any default values or domain definitions containing "a_plus"
SELECT 
    'ir_model_fields' as table_name,
    'domain' as column_name,
    id,
    domain as value
FROM ir_model_fields 
WHERE domain ILIKE '%a_plus%'

UNION ALL

SELECT 
    'ir_model_fields' as table_name,
    'default_value' as column_name,
    id,
    default_value as value
FROM ir_model_fields 
WHERE default_value ILIKE '%a_plus%';

-- Check for any data in ir_model_data that might contain "a_plus"
SELECT 
    'ir_model_data' as table_name,
    'name' as column_name,
    id,
    name as value
FROM ir_model_data 
WHERE name ILIKE '%a_plus%'

UNION ALL

SELECT 
    'ir_model_data' as table_name,
    'res_id' as column_name,
    id,
    res_id::text as value
FROM ir_model_data 
WHERE res_id::text ILIKE '%a_plus%';

-- Let's also check if there are any views or other database objects that might be causing issues
SELECT 
    'ir_ui_view' as table_name,
    'name' as column_name,
    id,
    name as value
FROM ir_ui_view 
WHERE name ILIKE '%a_plus%'

UNION ALL

SELECT 
    'ir_ui_view' as table_name,
    'arch' as column_name,
    id,
    SUBSTRING(arch, 1, 100) as value
FROM ir_ui_view 
WHERE arch ILIKE '%a_plus%';

-- Check for any configuration parameters that might contain "a_plus"
SELECT 
    'ir_config_parameter' as table_name,
    'key' as column_name,
    id,
    key as value
FROM ir_config_parameter 
WHERE key ILIKE '%a_plus%'

UNION ALL

SELECT 
    'ir_config_parameter' as table_name,
    'value' as column_name,
    id,
    value as value
FROM ir_config_parameter 
WHERE value ILIKE '%a_plus%'; 