-- Fix for missing itq.sister.company model
-- This script ensures the model is properly registered in the database

-- Check if the model exists in ir_model
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'itq.sister.company') THEN
        -- Insert the model if it doesn't exist
        INSERT INTO ir_model (name, model, state, transient, modules)
        VALUES ('Sister Company', 'itq.sister.company', 'base', false, 'payroll_base_account');
        
        RAISE NOTICE 'Added itq.sister.company model to ir_model';
    ELSE
        RAISE NOTICE 'Model itq.sister.company already exists in ir_model';
    END IF;
END $$;

-- Ensure the model's fields are properly registered
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ir_model_fields WHERE model = 'itq.sister.company' AND name = 'name') THEN
        -- Get the model ID
        INSERT INTO ir_model_fields (name, field_description, model, model_id, state, modules, ttype, required)
        SELECT 'name', 'Name', 'itq.sister.company', id, 'base', 'payroll_base_account', 'char', true
        FROM ir_model WHERE model = 'itq.sister.company';
        
        RAISE NOTICE 'Added name field to itq.sister.company model';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM ir_model_fields WHERE model = 'itq.sister.company' AND name = 'payroll_account_id') THEN
        -- Add the payroll_account_id field
        INSERT INTO ir_model_fields (name, field_description, model, model_id, state, modules, ttype, required, relation)
        SELECT 'payroll_account_id', 'Payroll Account', 'itq.sister.company', id, 'base', 'payroll_base_account', 'many2one', true, 'account.account'
        FROM ir_model WHERE model = 'itq.sister.company';
        
        RAISE NOTICE 'Added payroll_account_id field to itq.sister.company model';
    END IF;
END $$;

-- Create the table for the model if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'itq_sister_company') THEN
        CREATE TABLE itq_sister_company (
            id SERIAL PRIMARY KEY,
            create_uid INTEGER,
            create_date TIMESTAMP WITHOUT TIME ZONE,
            write_uid INTEGER,
            write_date TIMESTAMP WITHOUT TIME ZONE,
            name VARCHAR NOT NULL,
            payroll_account_id INTEGER NOT NULL
        );
        
        RAISE NOTICE 'Created itq_sister_company table';
    ELSE
        RAISE NOTICE 'Table itq_sister_company already exists';
    END IF;
END $$;

-- Update module dependencies if needed
UPDATE ir_module_dependency 
SET name = 'payroll_base_account' 
WHERE name = 'payroll_base_account' 
AND module_id IN (
    SELECT id FROM ir_module_module 
    WHERE name IN ('itq_sponsorship_transfer', 'itq_sponsorship_transfer_portal')
);

-- Clear cache to ensure changes take effect
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE '%assets%';
