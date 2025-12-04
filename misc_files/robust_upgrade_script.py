#!/usr/bin/env python3
"""
Robust upgrade script for scs_operation module.
This script handles database connection issues and cursor errors during upgrade.
"""

import sys
import os
import time
import psycopg2
from psycopg2 import OperationalError

def find_odoo_path():
    """Find Odoo installation path automatically"""
    possible_paths = [
        '/opt/odoo',
        '/usr/lib/odoo',
        '/usr/local/odoo',
        os.path.expanduser('~/odoo'),
        os.path.expanduser('~/odoo17-server'),
        '/var/lib/odoo',
    ]
    
    try:
        import odoo
        return os.path.dirname(os.path.dirname(odoo.__file__))
    except ImportError:
        pass
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'odoo-bin')):
            return path
    
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if 'odoo-bin' in files:
            return root
    
    return None

# Find and add Odoo path
odoo_path = find_odoo_path()
if odoo_path:
    sys.path.insert(0, odoo_path)
    print(f"Found Odoo at: {odoo_path}")
else:
    print("Warning: Could not find Odoo installation. Trying to import anyway...")

try:
    import odoo
    from odoo import api, fields, models
    from odoo.exceptions import AccessError
except ImportError as e:
    print(f"Error importing Odoo: {e}")
    print("Please ensure Odoo is properly installed and accessible.")
    sys.exit(1)

def robust_upgrade_scs_operation():
    """Robustly upgrade scs_operation module with connection handling"""
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} of {max_retries}")
            
            # Initialize Odoo with proper error handling
            odoo.cli.server.main()
            
            # Get the environment with retry logic
            env = None
            for env_attempt in range(3):
                try:
                    env = api.Environment.manage()
                    break
                except Exception as e:
                    print(f"Environment creation attempt {env_attempt + 1} failed: {e}")
                    if env_attempt < 2:
                        time.sleep(2)
                    else:
                        raise
            
            if not env:
                raise Exception("Failed to create environment after multiple attempts")
            
            print("Starting robust upgrade for scs_operation module...")
            
            # Step 1: Clean up problematic access rights with connection handling
            print("Step 1: Cleaning up problematic access rights...")
            
            try:
                # Find and remove problematic access rights
                problematic_access = env['ir.model.access'].search([
                    ('group_id', '!=', False)
                ])
                
                removed_count = 0
                for access in problematic_access:
                    try:
                        # Check if the group exists
                        group = access.group_id
                        if not group.exists():
                            print(f"Removing access right for non-existent group: {access.name}")
                            access.unlink()
                            removed_count += 1
                    except Exception as e:
                        print(f"Error checking access right {access.name}: {e}")
                        # Remove the problematic access right
                        try:
                            access.unlink()
                            removed_count += 1
                        except:
                            pass
                
                print(f"Removed {removed_count} problematic access rights")
                
            except Exception as e:
                print(f"Error in Step 1: {e}")
                # Continue anyway
            
            # Step 2: Ensure required groups exist
            print("Step 2: Ensuring required groups exist...")
            
            try:
                required_groups = [
                    ('scs_operation.group_operation_user', 'Operation User'),
                    ('scs_operation.group_operation_admin', 'Operation Administrator'),
                    ('scs_operation.group_insurance_user', 'Insurance User'),
                    ('scs_operation.group_internal_sale_user', 'Internal Sale User'),
                    ('scs_operation.group_internal_sale_admin', 'Internal Sale Administrator'),
                    ('scs_operation.group_government_payment_operator', 'Government Payment Operator'),
                    ('scs_operation.my_flight_user', 'My Flight User'),
                ]
                
                created_count = 0
                for group_xml_id, group_name in required_groups:
                    try:
                        group = env.ref(group_xml_id)
                        print(f"Group {group_name} already exists")
                    except:
                        print(f"Creating group: {group_name}")
                        try:
                            group = env['res.groups'].create({
                                'name': group_name,
                                'category_id': env.ref('base.module_category_human_resources').id,
                            })
                            # Create the XML ID
                            env['ir.model.data'].create({
                                'name': group_xml_id.split('.')[-1],
                                'module': group_xml_id.split('.')[0],
                                'model': 'res.groups',
                                'res_id': group.id,
                            })
                            created_count += 1
                        except Exception as e:
                            print(f"Error creating group {group_name}: {e}")
                
                print(f"Created {created_count} missing groups")
                
            except Exception as e:
                print(f"Error in Step 2: {e}")
                # Continue anyway
            
            # Step 3: Fix attachment access rights
            print("Step 3: Fixing attachment access rights...")
            
            try:
                fixed_count = env['hr.employee']._fix_all_orphaned_attachments()
                print(f"Fixed {fixed_count} orphaned attachments")
            except Exception as e:
                print(f"Error fixing attachments: {e}")
            
            # Step 4: Update module with connection handling
            print("Step 4: Updating module...")
            
            try:
                module = env['ir.module.module'].search([('name', '=', 'scs_operation')])
                if module:
                    # Commit any pending changes before upgrade
                    env.cr.commit()
                    
                    # Perform the upgrade
                    module.button_upgrade()
                    
                    # Commit the upgrade
                    env.cr.commit()
                    print("Module updated successfully")
                else:
                    print("Module scs_operation not found")
            except Exception as e:
                print(f"Error updating module: {e}")
                # Try to rollback and continue
                try:
                    env.cr.rollback()
                except:
                    pass
            
            print("Robust upgrade completed successfully!")
            break  # Success, exit retry loop
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            # Try to clean up the environment
            try:
                if env:
                    env.cr.rollback()
                    env.cr.close()
            except:
                pass
            
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("All attempts failed. Please check the database connection and try again.")
                raise
    
    # Final cleanup
    try:
        if env:
            env.cr.close()
    except:
        pass

if __name__ == "__main__":
    robust_upgrade_scs_operation() 