-- Fix for module dependency issues
-- This script updates the module states to ensure proper loading

-- First, set itq_period to installed state
UPDATE ir_module_module 
SET state = 'installed' 
WHERE name = 'itq_period';

-- Then set payroll_base and payroll_base_account to to_upgrade state
-- This will trigger a registry rebuild for these modules
UPDATE ir_module_module 
SET state = 'to upgrade' 
WHERE name IN ('payroll_base', 'payroll_base_account');

-- Clear all caches
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE '%assets%';

-- Verify the module states
SELECT name, state FROM ir_module_module 
WHERE name IN ('itq_period', 'payroll_base', 'payroll_base_account', 'hr_employee_checklist')
ORDER BY name;
