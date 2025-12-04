-- Convert varchar columns to integer to prevent conversion errors
-- This should be run before the Odoo migration

-- First, let's check the current state
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
AND table_name IN ('logistic_order', 'logistic_order_line', 'employee_insurance_line')
AND column_name IN ('insurance_class', 'insurance_policy_id', 'insurance_class_id')
ORDER BY table_name, column_name;

-- Convert logistic_order.insurance_class from varchar to integer
-- Since the column is empty, we can safely convert it
ALTER TABLE logistic_order 
ALTER COLUMN insurance_class TYPE integer USING 
  CASE 
    WHEN insurance_class IS NULL THEN NULL
    WHEN insurance_class ~ '^[0-9]+$' THEN insurance_class::integer
    ELSE NULL
  END;

-- Convert logistic_order_line.insurance_class from varchar to integer
ALTER TABLE logistic_order_line 
ALTER COLUMN insurance_class TYPE integer USING 
  CASE 
    WHEN insurance_class IS NULL THEN NULL
    WHEN insurance_class ~ '^[0-9]+$' THEN insurance_class::integer
    ELSE NULL
  END;

-- Verify the conversion worked
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
AND table_name IN ('logistic_order', 'logistic_order_line', 'employee_insurance_line')
AND column_name IN ('insurance_class', 'insurance_policy_id', 'insurance_class_id')
ORDER BY table_name, column_name; 