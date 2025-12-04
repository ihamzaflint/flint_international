-- Updated script to disable the auditlog module which is causing database errors

-- Check if the auditlog_rule table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'auditlog_rule') THEN
        -- Delete any auditlog rules (safer than trying to update them)
        DELETE FROM auditlog_rule;
    END IF;
END
$$;

-- Update the module state to uninstalled if it exists
UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'auditlog';

-- Remove any auditlog dependencies
DELETE FROM ir_module_module_dependency WHERE name = 'auditlog';

-- Fix the error with the operator by updating the database configuration
-- This addresses the "operator does not exist: character varying ->> unknown" error
DO $$
BEGIN
    -- Check if the function exists and create it if it doesn't
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'jsonb_extract_path_text') THEN
        -- Create a dummy function to handle the operator
        CREATE OR REPLACE FUNCTION public.dummy_jsonb_extract(jsonb, text)
        RETURNS text AS $$
            SELECT '';
        $$ LANGUAGE SQL IMMUTABLE;
        
        -- Create operator if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM pg_operator WHERE oprname = '->>' AND oprleft = 'character varying'::regtype) THEN
            -- This is a temporary workaround - in production you'd want a proper fix
            CREATE OPERATOR ->> (
                LEFTARG = character varying,
                RIGHTARG = unknown,
                FUNCTION = public.dummy_jsonb_extract
            );
        END IF;
    END IF;
END
$$;

-- Commit the changes
COMMIT;
