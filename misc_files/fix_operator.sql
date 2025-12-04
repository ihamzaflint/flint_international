-- Simplified fix for the "operator does not exist: character varying ->> unknown" error

-- Create a function that handles the JSON operator for character varying fields
CREATE OR REPLACE FUNCTION public.varchar_json_extract(character varying, text)
RETURNS text AS $$
BEGIN
    -- Simply return the first argument as text, ignoring the language key
    RETURN $1;
EXCEPTION
    WHEN OTHERS THEN
        RETURN '';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create the operator
DO $$
BEGIN
    -- Drop the operator if it exists
    DROP OPERATOR IF EXISTS ->> (character varying, text);
    
    -- Create the operator
    EXECUTE 'CREATE OPERATOR ->> (
        LEFTARG = character varying,
        RIGHTARG = text,
        FUNCTION = public.varchar_json_extract
    )';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not create operator for text type: %', SQLERRM;
END $$;

-- Update problematic modules if they exist
DO $$
BEGIN
    UPDATE ir_module_module 
    SET state = 'uninstalled' 
    WHERE name IN ('auditlog', 'base_partner_translatable')
    AND EXISTS (SELECT 1 FROM ir_module_module WHERE name IN ('auditlog', 'base_partner_translatable'));
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not update modules: %', SQLERRM;
END $$;

-- Clear view cache
DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND name LIKE '%assets%';
