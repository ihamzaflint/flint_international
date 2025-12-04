#!/usr/bin/env python3
"""
Script to fix orphaned attachments in hr.employee records.
This script fixes attachments that have res_id = 0 and links them to the correct employee.
"""

import sys
import os

# Try to find Odoo path automatically
def find_odoo_path():
    """Find Odoo installation path automatically"""
    # Common Odoo installation paths
    possible_paths = [
        '/opt/odoo',  # Common Linux installation
        '/usr/lib/odoo',  # Debian/Ubuntu package installation
        '/usr/local/odoo',  # Manual installation
        os.path.expanduser('~/odoo'),  # User home directory
        os.path.expanduser('~/odoo17-server'),  # Local development
        '/var/lib/odoo',  # Another common location
    ]
    
    # Check if we're already in an Odoo environment
    try:
        import odoo
        return os.path.dirname(os.path.dirname(odoo.__file__))
    except ImportError:
        pass
    
    # Try to find odoo-bin in common paths
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'odoo-bin')):
            return path
    
    # If not found, try to find it in current directory or parent directories
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if 'odoo-bin' in files:
            return root
    
    # Last resort: try to find it in PATH
    import subprocess
    try:
        result = subprocess.run(['which', 'odoo-bin'], capture_output=True, text=True)
        if result.returncode == 0:
            odoo_bin_path = result.stdout.strip()
            return os.path.dirname(odoo_bin_path)
    except:
        pass
    
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


def fix_orphaned_attachments():
    """Fix orphaned attachments in the system"""
    
    try:
        # Initialize Odoo with proper configuration
        # For Odoo.sh, we need to handle configuration differently
        import argparse
        
        # Set up argument parser for Odoo configuration
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', help='Configuration file')
        parser.add_argument('--database', help='Database name')
        parser.add_argument('--db_host', help='Database host')
        parser.add_argument('--db_port', help='Database port')
        parser.add_argument('--db_user', help='Database user')
        parser.add_argument('--db_password', help='Database password')
        
        # Parse command line arguments
        args, unknown = parser.parse_known_args()
        
        # Set up Odoo configuration
        odoo_config = {}
        if args.config:
            odoo_config['config_file'] = args.config
        if args.database:
            odoo_config['db_name'] = args.database
        if args.db_host:
            odoo_config['db_host'] = args.db_host
        if args.db_port:
            odoo_config['db_port'] = args.db_port
        if args.db_user:
            odoo_config['db_user'] = args.db_user
        if args.db_password:
            odoo_config['db_password'] = args.db_password
        
        # Initialize Odoo
        odoo.cli.server.main()
        
        # Get the environment
        env = api.Environment.manage()
        
        # Find orphaned attachments
        orphaned_attachments = env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', 0),
        ])
        
        print(f"Found {len(orphaned_attachments)} orphaned attachments")
        
        fixed_count = 0
        for attachment in orphaned_attachments:
            # Try to find the employee by checking if the attachment is in their passport_copy field
            employee = env['hr.employee'].sudo().search([
                ('passport_copy', 'in', attachment.id)
            ], limit=1)
            
            if employee:
                attachment.write({
                    'res_id': employee.id,
                    'public': True,
                })
                fixed_count += 1
                print(f"Fixed attachment {attachment.id} -> Employee {employee.id} ({employee.name})")
            else:
                print(f"Could not find employee for attachment {attachment.id}")
        
        print(f"Fixed {fixed_count} attachments out of {len(orphaned_attachments)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            env.cr.close()
        except:
            pass


if __name__ == "__main__":
    fix_orphaned_attachments() 