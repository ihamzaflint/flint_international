-- Fix insurance_class_from and insurance_class_to columns
-- These should be Many2one fields but contain string values

-- Check current state
SELECT 'logistic_order' as table_name, 'insurance_class_from' as column_name, id, insurance_class_from as value
FROM logistic_order 
WHERE insurance_class_from IS NOT NULL AND insurance_class_from !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_to' as column_name, id, insurance_class_to as value
FROM logistic_order 
WHERE insurance_class_to IS NOT NULL AND insurance_class_to !~ '^[0-9]+$';

-- Fix the non-integer values
UPDATE logistic_order 
SET insurance_class_from = NULL 
WHERE insurance_class_from IS NOT NULL AND insurance_class_from !~ '^[0-9]+$';

UPDATE logistic_order 
SET insurance_class_to = NULL 
WHERE insurance_class_to IS NOT NULL AND insurance_class_to !~ '^[0-9]+$';

-- Convert the columns to integer type
ALTER TABLE logistic_order 
ALTER COLUMN insurance_class_from TYPE integer USING 
  CASE 
    WHEN insurance_class_from IS NULL THEN NULL
    WHEN insurance_class_from ~ '^[0-9]+$' THEN insurance_class_from::integer
    ELSE NULL
  END;

ALTER TABLE logistic_order 
ALTER COLUMN insurance_class_to TYPE integer USING 
  CASE 
    WHEN insurance_class_to IS NULL THEN NULL
    WHEN insurance_class_to ~ '^[0-9]+$' THEN insurance_class_to::integer
    ELSE NULL
  END;

-- Verify the fix worked
SELECT 'logistic_order' as table_name, 'insurance_class_from' as column_name, id, insurance_class_from::text as value
FROM logistic_order 
WHERE insurance_class_from IS NOT NULL AND insurance_class_from::text !~ '^[0-9]+$'
UNION ALL
SELECT 'logistic_order' as table_name, 'insurance_class_to' as column_name, id, insurance_class_to::text as value
FROM logistic_order 
WHERE insurance_class_to IS NOT NULL AND insurance_class_to::text !~ '^[0-9]+$';

-- Check the column types
SELECT table_name, column_name, data_type
FROM information_schema.columns 
WHERE table_schema = 'public'
AND table_name = 'logistic_order'
AND column_name IN ('insurance_class_from', 'insurance_class_to')
ORDER BY column_name; 