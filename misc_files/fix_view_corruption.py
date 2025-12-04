#!/usr/bin/env python3
"""
Script to fix corrupted ir.ui.view records that cause XML parsing errors.
Run this script from your Odoo server directory.
"""
import os
import sys
import logging

# Add Odoo to path
sys.path.append('/Users/omarkhaled/odoo/odoo17-server')

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

# Configure logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

def fix_corrupted_views(database_name):
    """Fix corrupted views in the database."""
    try:
        # Initialize Odoo
        config['db_name'] = database_name
        odoo.service.db._drop_conn()
        
        # Get registry and environment
        registry = odoo.registry(database_name)
        
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            
            # Find corrupted views
            corrupted_views = env['ir.ui.view'].search([
                ('model', '=', 'hr.employee'),
                '|', '|', '|',
                ('arch', '=', False),
                ('arch', '=', ''),
                ('arch', '=', 'False'),
                ('arch', '=', 'True')
            ])
            
            if corrupted_views:
                _logger.info(f"Found {len(corrupted_views)} corrupted views")
                for view in corrupted_views:
                    _logger.info(f"Deleting corrupted view: {view.name} (ID: {view.id})")
                    view.unlink()
                    
                cr.commit()
                _logger.info("Corrupted views deleted successfully")
            else:
                _logger.info("No corrupted views found")
                
            # Also check for views with invalid XML
            all_hr_views = env['ir.ui.view'].search([('model', '=', 'hr.employee')])
            for view in all_hr_views:
                if view.arch:
                    try:
                        from lxml import etree
                        etree.fromstring(view.arch)
                    except Exception as e:
                        _logger.error(f"Invalid XML in view {view.name} (ID: {view.id}): {e}")
                        # Optionally delete or fix the view
                        # view.unlink()
                        
    except Exception as e:
        _logger.error(f"Error fixing views: {e}")
        return False
    
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 fix_view_corruption.py <database_name>")
        sys.exit(1)
        
    database_name = sys.argv[1]
    success = fix_corrupted_views(database_name)
    
    if success:
        print("View corruption fix completed. Please restart your Odoo server.")
    else:
        print("Failed to fix view corruption. Check the logs for details.")
