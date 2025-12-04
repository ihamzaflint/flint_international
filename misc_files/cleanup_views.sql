-- SQL script to identify and clean up corrupted views
-- Run this in your PostgreSQL database

-- 1. Find views with invalid arch content
SELECT id, name, model, 
       CASE 
           WHEN arch IS NULL THEN 'NULL'
           WHEN arch = '' THEN 'EMPTY'
           WHEN arch = 'False' THEN 'FALSE_STRING'
           WHEN arch = 'True' THEN 'TRUE_STRING'
           ELSE 'OTHER'
       END as issue_type
FROM ir_ui_view 
WHERE model = 'hr.employee' 
AND (arch IS NULL OR arch = '' OR arch = 'False' OR arch = 'True');

-- 2. Delete corrupted views (BACKUP YOUR DATABASE FIRST!)
-- DELETE FROM ir_ui_view 
-- WHERE model = 'hr.employee' 
-- AND (arch IS NULL OR arch = '' OR arch = 'False' OR arch = 'True');

-- 3. Find views that might have invalid XML (requires manual inspection)
SELECT id, name, model, length(arch) as arch_length
FROM ir_ui_view 
WHERE model = 'hr.employee' 
AND arch IS NOT NULL 
AND arch != ''
ORDER BY arch_length;

-- 4. Reset all hr.employee views to default (DANGER: Will remove customizations)
-- DELETE FROM ir_ui_view WHERE model = 'hr.employee' AND key LIKE '%hr.employee%';
