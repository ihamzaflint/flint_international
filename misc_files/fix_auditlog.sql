-- Script to disable the auditlog module which is causing database errors

-- First, disable any active auditlog rules
UPDATE auditlog_rule SET active = FALSE;

-- Update the module state to uninstalled
UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'auditlog';

-- Remove any auditlog dependencies
DELETE FROM ir_module_module_dependency WHERE name = 'auditlog';

-- Commit the changes
COMMIT;
