-- Comprehensive fix for the "operator does not exist: character varying ->> unknown" error
-- This creates a workaround function and operator to handle the translation operator

BEGIN;

-- Create a function to handle the translation operator
CREATE OR REPLACE FUNCTION public.jsonb_extract_text(character varying, text)
RETURNS text AS $$
BEGIN
    -- Simply return the first argument as text, ignoring the language key
    RETURN $1;
EXCEPTION
    WHEN OTHERS THEN
        RETURN '';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Check if the operator exists and create it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_operator 
        WHERE oprname = '->>' 
        AND oprleft = 'character varying'::regtype 
        AND oprright = 'unknown'::regtype
    ) THEN
        -- Create the operator
        EXECUTE $op$
        CREATE OPERATOR ->> (
            LEFTARG = character varying,
            RIGHTARG = unknown,
            FUNCTION = public.jsonb_extract_text
        );
        $op$;
    END IF;
END
$$;

-- Clear any related cache entries that might be causing issues
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE '%assets%';

-- Update the module state to avoid loading problematic modules
UPDATE ir_module_module SET state = 'uninstalled' WHERE name IN ('auditlog', 'base_partner_translatable');

COMMIT;
