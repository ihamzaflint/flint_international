-- Script to clean up references to itq.service.portal.configuration
-- This will remove any database references to the model that's causing issues

-- First, identify and delete any ir.model.data records pointing to the model
DELETE FROM ir_model_data 
WHERE model = 'ir.model' 
AND res_id IN (
    SELECT id FROM ir_model WHERE model = 'itq.service.portal.configuration'
);

-- Delete any model access rights for this model
DELETE FROM ir_model_access 
WHERE model_id IN (
    SELECT id FROM ir_model WHERE model = 'itq.service.portal.configuration'
);

-- Delete any model constraints for this model
DELETE FROM ir_model_constraint 
WHERE model IN (
    SELECT id FROM ir_model WHERE model = 'itq.service.portal.configuration'
);

-- Delete any model relations for this model
DELETE FROM ir_model_relation 
WHERE model IN (
    SELECT id FROM ir_model WHERE model = 'itq.service.portal.configuration'
);

-- Delete any model fields for this model
DELETE FROM ir_model_fields 
WHERE model_id IN (
    SELECT id FROM ir_model WHERE model = 'itq.service.portal.configuration'
);

-- Finally, delete the model itself
DELETE FROM ir_model 
WHERE model = 'itq.service.portal.configuration';

-- Commit the changes
COMMIT;
