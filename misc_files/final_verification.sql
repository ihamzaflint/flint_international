-- Final verification script to ensure all insurance-related columns are properly typed
-- and contain no invalid data that could cause conversion errors

-- Check all insurance-related columns for their data types
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
AND table_name IN ('logistic_order', 'logistic_order_line', 'employee_insurance_line', 'helpdesk_ticket')
AND column_name ILIKE '%insurance%'
ORDER BY table_name, column_name;

-- Check for any remaining non-integer values in columns that should be integers
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

-- Check for any values containing "a" or "a_plus" in any insurance-related column
SELECT 'logistic_order' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a%'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_from' as column_name, id, insurance_class_from::text as value
FROM logistic_order 
WHERE insurance_class_from IS NOT NULL AND insurance_class_from::text ILIKE '%a%'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_to' as column_name, id, insurance_class_to::text as value
FROM logistic_order 
WHERE insurance_class_to IS NOT NULL AND insurance_class_to::text ILIKE '%a%'
UNION ALL
SELECT 'logistic_order_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM logistic_order_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a%'
UNION ALL
SELECT 'employee_insurance_line' as table_name, 'insurance_class' as column_name, id, insurance_class::text as value
FROM employee_insurance_line 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a%'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_from_id' as column_name, id, insurance_class_from_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_from_id IS NOT NULL AND insurance_class_from_id::text ILIKE '%a%'
UNION ALL
SELECT 'helpdesk_ticket' as table_name, 'insurance_class_to_id' as column_name, id, insurance_class_to_id::text as value
FROM helpdesk_ticket 
WHERE insurance_class_to_id IS NOT NULL AND insurance_class_to_id::text ILIKE '%a%';

-- Summary of what should be integer columns
SELECT 'Expected integer columns:' as info;
SELECT 'logistic_order.insurance_class' as expected_integer_column
UNION ALL
SELECT 'logistic_order.insurance_class_from'
UNION ALL
SELECT 'logistic_order.insurance_class_to'
UNION ALL
SELECT 'logistic_order_line.insurance_class'
UNION ALL
SELECT 'employee_insurance_line.insurance_class'
UNION ALL
SELECT 'helpdesk_ticket.insurance_class_from_id'
UNION ALL
SELECT 'helpdesk_ticket.insurance_class_to_id'; 