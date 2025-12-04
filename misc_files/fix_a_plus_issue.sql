-- SQL script to find and fix "a_plus" and other non-integer values
-- Run this directly on your database before the migration

-- First, let's find where "a_plus" is stored
SELECT 'logistic_order' as table_name, column_name, id, 
       CASE WHEN column_name = 'insurance_policy_id' THEN insurance_policy_id
            WHEN column_name = 'insurance_class' THEN insurance_class
            ELSE NULL END as value
FROM (
    SELECT 'insurance_policy_id' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM logistic_order 
    WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
    UNION ALL
    SELECT 'insurance_class' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM logistic_order 
    WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
) subq;

-- Check employee_insurance_line table
SELECT 'employee_insurance_line' as table_name, column_name, id, 
       CASE WHEN column_name = 'insurance_policy_id' THEN insurance_policy_id
            WHEN column_name = 'insurance_class' THEN insurance_class
            ELSE NULL END as value
FROM (
    SELECT 'insurance_policy_id' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM employee_insurance_line 
    WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
    UNION ALL
    SELECT 'insurance_class' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM employee_insurance_line 
    WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
) subq;

-- Check logistic_order_line table
SELECT 'logistic_order_line' as table_name, column_name, id, 
       CASE WHEN column_name = 'insurance_policy_id' THEN insurance_policy_id
            WHEN column_name = 'insurance_class' THEN insurance_class
            ELSE NULL END as value
FROM (
    SELECT 'insurance_policy_id' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM logistic_order_line 
    WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%'
    UNION ALL
    SELECT 'insurance_class' as column_name, id, insurance_policy_id::text as insurance_policy_id, insurance_class::text as insurance_class
    FROM logistic_order_line 
    WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%'
) subq;

-- Now fix the issues by setting problematic values to NULL
-- Logistic Order
UPDATE logistic_order 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE logistic_order 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- Employee Insurance Line
UPDATE employee_insurance_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE employee_insurance_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- Logistic Order Line
UPDATE logistic_order_line 
SET insurance_policy_id = NULL 
WHERE insurance_policy_id IS NOT NULL AND insurance_policy_id::text ILIKE '%a_plus%';

UPDATE logistic_order_line 
SET insurance_class = NULL 
WHERE insurance_class IS NOT NULL AND insurance_class::text ILIKE '%a_plus%';

-- Also fix any other non-integer values in these columns
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

-- Drop the insurance_policy column if it exists
ALTER TABLE logistic_order DROP COLUMN IF EXISTS insurance_policy; 