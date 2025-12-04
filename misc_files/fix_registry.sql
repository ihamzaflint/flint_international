-- Fix for missing itq.sister.company model in registry
-- This script updates the module registry and clears caches

-- Update the module state to trigger a registry rebuild
UPDATE ir_module_module 
SET state = 'to upgrade' 
WHERE name = 'payroll_base_account';

-- Clear all caches
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE '%assets%';

-- Ensure the model is properly registered
UPDATE ir_model
SET state = 'manual'
WHERE model = 'itq.sister.company';

-- Check if the model exists and is properly configured
SELECT model, name, state, modules
FROM ir_model
WHERE model = 'itq.sister.company';

-- Check if the fields are properly registered
SELECT name, field_description, ttype, required
FROM ir_model_fields
WHERE model = 'itq.sister.company'
ORDER BY name;
