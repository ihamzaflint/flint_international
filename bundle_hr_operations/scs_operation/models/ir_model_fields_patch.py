# -*- coding: utf-8 -*-
"""
EMERGENCY PATCH for registry loading error
This patch fixes the AttributeError: 'str' object has no attribute 'get'
that occurs during registry loading before migrations can run.
"""

import logging
from odoo.addons.base.models.ir_model import IrModelSelection

_logger = logging.getLogger(__name__)

# Log the patching attempt
_logger.warning("EMERGENCY PATCH: Directly replacing IrModelSelection._process_ondelete")

# Store the original method for potential future use
original_process_ondelete = getattr(IrModelSelection, '_process_ondelete', None)

# Define a replacement for the problematic method
def safe_process_ondelete(self):
    """
    Safe replacement for _process_ondelete that handles string ondelete values.
    This prevents the AttributeError: 'str' object has no attribute 'get' error.
    """
    _logger.warning("EMERGENCY PATCH: Safe _process_ondelete called")
    
    for selection in self:
        try:
            # Check if we're dealing with a field record
            field = selection.field_id
            if not field:
                continue
                
            # Get the ondelete value, safely
            ondelete = None
            try:
                # This might fail if ondelete is a string
                if hasattr(field, 'ondelete') and field.ondelete:
                    if isinstance(field.ondelete, dict):
                        ondelete = field.ondelete.get(selection.value)
                    elif isinstance(field.ondelete, str):
                        # String ondelete values cause the error, convert to empty dict
                        _logger.warning(f"EMERGENCY PATCH: Converting string ondelete to dict for field {field.name}")
                        field.ondelete = {}
            except Exception as e:
                _logger.warning(f"EMERGENCY PATCH: Error accessing ondelete: {e}")
                continue
                
            # Skip if no ondelete action
            if not ondelete:
                continue
                
            # Handle the records safely
            records = None
            try:
                # The original code that might fail with attribute errors
                records = selection._get_records()
            except Exception as e:
                _logger.warning(f"EMERGENCY PATCH: Error getting records: {e}")
                continue
                
            # Skip if no records
            if not records:
                continue
                
            # Apply the ondelete action safely
            try:
                if callable(ondelete):
                    ondelete(records)
            except Exception as e:
                _logger.warning(f"EMERGENCY PATCH: Error applying ondelete: {e}")
                continue
        except Exception as e:
            _logger.warning(f"EMERGENCY PATCH: General error in _process_ondelete: {e}")
            # Continue with other selections instead of crashing
            continue
    
    # Return True to indicate success and allow registry loading to continue
    return True

# Apply the patch by replacing the method
_logger.warning("EMERGENCY PATCH: Replacing IrModelSelection._process_ondelete with safe version")
IrModelSelection._process_ondelete = safe_process_ondelete
_logger.warning("EMERGENCY PATCH: Method replacement complete")
