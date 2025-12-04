#!/usr/bin/env python3
"""
Safe script to fix corrupted hr.employee views without stopping the server.
This script uses Odoo's XML-RPC interface to safely fix the views.
"""
import xmlrpc.client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

def fix_views_via_xmlrpc():
    """Fix corrupted views using XML-RPC interface."""
    try:
        # Connect to your Odoo server (adjust URL, database, username, password as needed)
        url = 'http://localhost:8069'
        db = 'your_database_name'  # Replace with your actual database name
        username = 'admin'  # Replace with your admin username
        password = 'admin'  # Replace with your admin password
        
        # Get the common interface
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        
        # Authenticate
        uid = common.authenticate(db, username, password, {})
        if not uid:
            _logger.error("Authentication failed")
            return False
            
        # Get the object interface
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Search for potentially corrupted views
        view_ids = models.execute_kw(db, uid, password,
            'ir.ui.view', 'search',
            [[['model', '=', 'hr.employee']]])
        
        _logger.info(f"Found {len(view_ids)} hr.employee views")
        
        corrupted_count = 0
        for view_id in view_ids:
            try:
                # Read the view
                view_data = models.execute_kw(db, uid, password,
                    'ir.ui.view', 'read',
                    [view_id], {'fields': ['name', 'arch', 'model']})
                
                if view_data:
                    view = view_data[0]
                    arch = view.get('arch', '')
                    
                    # Check if arch is invalid
                    if not arch or arch in ['False', 'True', '']:
                        _logger.info(f"Found corrupted view: {view['name']} (ID: {view_id})")
                        
                        # Try to delete the corrupted view
                        models.execute_kw(db, uid, password,
                            'ir.ui.view', 'unlink', [view_id])
                        
                        corrupted_count += 1
                        _logger.info(f"Deleted corrupted view: {view['name']}")
                        
                    elif arch:
                        # Test if arch is valid XML
                        try:
                            from lxml import etree
                            etree.fromstring(arch)
                        except Exception as xml_error:
                            _logger.warning(f"Invalid XML in view {view['name']}: {xml_error}")
                            # Optionally delete or fix
                            
            except Exception as e:
                _logger.error(f"Error processing view {view_id}: {e}")
                continue
        
        _logger.info(f"Processed {len(view_ids)} views, fixed {corrupted_count} corrupted views")
        
        # Force view cache refresh
        models.execute_kw(db, uid, password,
            'ir.ui.view', 'clear_caches', [])
        
        return True
        
    except Exception as e:
        _logger.error(f"Error in XML-RPC fix: {e}")
        return False

if __name__ == '__main__':
    print("Attempting to fix corrupted hr.employee views...")
    success = fix_views_via_xmlrpc()
    
    if success:
        print("✅ View corruption fix completed successfully!")
        print("Please refresh your browser and try accessing HR employees again.")
    else:
        print("❌ Failed to fix view corruption.")
        print("You may need to check your database connection settings or run the SQL cleanup script.")
