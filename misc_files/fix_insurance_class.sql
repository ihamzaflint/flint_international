-- Fix Insurance Class is_active Field
-- Run this script to resolve the "is_active field is undefined" error

-- Step 1: Add is_active column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insurance_class' 
        AND column_name = 'is_active'
    ) THEN
        ALTER TABLE insurance_class ADD COLUMN is_active boolean DEFAULT true;
        RAISE NOTICE 'Added is_active column to insurance_class table';
    ELSE
        RAISE NOTICE 'is_active column already exists';
    END IF;
END $$;

-- Step 2: Update existing records to have is_active = active
UPDATE insurance_class 
SET is_active = COALESCE(active, true) 
WHERE is_active IS NULL;

-- Step 3: Verify the fix
SELECT 
    id,
    name,
    active,
    is_active,
    CASE 
        WHEN is_active IS NULL THEN 'NEEDS FIX'
        WHEN is_active = active THEN 'OK'
        ELSE 'MISMATCH'
    END as status
FROM insurance_class 
ORDER BY id;

-- Step 4: Show summary
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_active IS NOT NULL THEN 1 END) as records_with_is_active,
    COUNT(CASE WHEN is_active IS NULL THEN 1 END) as records_needing_fix
FROM insurance_class; 