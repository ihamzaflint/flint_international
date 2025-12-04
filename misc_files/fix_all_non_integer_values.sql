-- Comprehensive fix for ALL non-integer values in insurance-related columns
-- This script will find and fix any non-integer values that might cause conversion errors

-- First, let's find ALL non-integer values in insurance-related columns
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

-- Now fix all non-integer values by setting them to NULL
UPDATE logistic_order 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

UPDATE logistic_order_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

-- Also check for any other insurance-related columns that might have non-integer values
-- Check insurance_policy_id columns
SELECT 'logistic_order' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM employee_insurance_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_policy_id' as column_name, id, insurance_policy_id::text as value
FROM logistic_order_line 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

-- Fix insurance_policy_id columns
UPDATE logistic_order 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE employee_insurance_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

UPDATE logistic_order_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text !~ '^[0-9]+$';

-- Check for any other insurance-related columns that might exist
-- This will help us find any other columns we might have missed
SELECT table_name, column_name, data_type
FROM information_schema.columns 
WHERE table_schema = 'public'
AND table_name IN ('logistic_order', 'logistic_order_line', 'employee_insurance_line', 'helpdesk_ticket')
AND column_name ILIKE '%insurance%'
ORDER BY table_name, column_name;

-- Verify the fix worked by checking for any remaining non-integer values
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text !~ '^[0-9]+$';

-- If the above query returns no rows, the fix was successful 