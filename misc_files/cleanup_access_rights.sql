-- Cleanup script for problematic access rights
-- Run this before upgrading the scs_operation module

-- Step 1: Find access rights that reference non-existent groups
SELECT 
    ima.id,
    ima.name,
    ima.model,
    ima.group_id,
    rg.name as group_name
FROM ir_model_access ima
LEFT JOIN res_groups rg ON ima.group_id = rg.id
WHERE ima.group_id IS NOT NULL 
AND rg.id IS NULL;

-- Step 2: Remove access rights that reference non-existent groups
DELETE FROM ir_model_access 
WHERE group_id IN (
    SELECT ima.group_id 
    FROM ir_model_access ima
    LEFT JOIN res_groups rg ON ima.group_id = rg.id
    WHERE ima.group_id IS NOT NULL 
    AND rg.id IS NULL
);

-- Step 3: Remove access rights for scs_operation custom groups that might not exist
DELETE FROM ir_model_access 
WHERE name LIKE '%scs_operation%' 
AND group_id IN (
    SELECT id FROM res_groups 
    WHERE name IN (
        'Operation User',
        'Operation Administrator', 
        'Insurance User',
        'Internal Sale User',
        'Internal Sale Administrator',
        'Government Payment Operator',
        'My Flight User'
    )
);

-- Step 4: Clean up any orphaned access rights for the new wizard
DELETE FROM ir_model_access 
WHERE name LIKE '%fix_attachments_wizard%';

-- Step 5: Verify cleanup
SELECT 
    ima.id,
    ima.name,
    ima.model,
    ima.group_id,
    rg.name as group_name
FROM ir_model_access ima
LEFT JOIN res_groups rg ON ima.group_id = rg.id
WHERE ima.name LIKE '%scs_operation%' 
OR ima.name LIKE '%fix_attachments%';

-- Step 6: Create missing groups if they don't exist
INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Operation User',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Users with basic operation access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Operation User');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Operation Administrator',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Administrators with full operation access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Operation Administrator');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Insurance User',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Users with insurance-related access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Insurance User');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Internal Sale User',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Users with internal sale access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Internal Sale User');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Internal Sale Administrator',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Administrators with internal sale access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Internal Sale Administrator');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'Government Payment Operator',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Operators with government payment access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'Government Payment Operator');

INSERT INTO res_groups (name, category_id, comment, create_uid, create_date, write_uid, write_date)
SELECT 
    'My Flight User',
    (SELECT id FROM ir_module_category WHERE name = 'Human Resources' LIMIT 1),
    'Users with flight booking access',
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM res_groups WHERE name = 'My Flight User');

-- Step 7: Create XML IDs for the groups
INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_operation_user',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Operation User'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_operation_user' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_operation_admin',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Operation Administrator'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_operation_admin' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_insurance_user',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Insurance User'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_insurance_user' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_internal_sale_user',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Internal Sale User'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_internal_sale_user' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_internal_sale_admin',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Internal Sale Administrator'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_internal_sale_admin' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'group_government_payment_operator',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'Government Payment Operator'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'group_government_payment_operator' AND module = 'scs_operation');

INSERT INTO ir_model_data (name, module, model, res_id, create_uid, create_date, write_uid, write_date)
SELECT 
    'my_flight_user',
    'scs_operation',
    'res.groups',
    id,
    1, NOW(), 1, NOW()
FROM res_groups 
WHERE name = 'My Flight User'
AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE name = 'my_flight_user' AND module = 'scs_operation');

-- Step 8: Verify the cleanup
SELECT 'Cleanup completed successfully' as status; 