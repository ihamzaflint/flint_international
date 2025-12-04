# Attachment Access Rights Guide

## Problem Description
Some users are still having issues accessing employee records after the attachment fix. This is likely due to missing access rights or group memberships.

## Required Groups for Attachment Access

### 1. Core HR Groups
- **`hr.group_hr_user`** - Basic HR user access
- **`hr.group_hr_manager`** - HR manager access (full permissions)

### 2. Base Groups
- **`base.group_user`** - Basic user access
- **`base.group_erp_manager`** - Administrator access

### 3. Custom Operation Groups (if applicable)
- **`scs_operation.group_operation_user`** - Operation user access
- **`scs_operation.group_operation_admin`** - Operation admin access

## Access Rights Configuration

### For Employee Records:
- **Read Access**: All users with `hr.group_hr_user`
- **Write Access**: Users with `hr.group_hr_user` or `hr.group_hr_manager`
- **Create Access**: Users with `hr.group_hr_manager`
- **Delete Access**: Users with `hr.group_hr_manager`

### For Attachments:
- **Read Access**: All users (attachments are public)
- **Write Access**: Users who created the attachment or HR managers
- **Create Access**: All HR users
- **Delete Access**: HR managers or attachment creator

## Troubleshooting Steps

### 1. Check User Groups
```python
# In Odoo shell or server action
user = env['res.users'].browse(user_id)
print("User groups:", user.groups_id.mapped('name'))
```

### 2. Verify Attachment Access
```python
# Check if attachments are properly linked
orphaned = env['ir.attachment'].search([
    ('res_model', '=', 'hr.employee'),
    ('res_id', '=', 0)
])
print(f"Orphaned attachments: {len(orphaned)}")
```

### 3. Fix Attachment Access Rights
```python
# Run this to fix all attachment access rights
env['hr.employee']._check_attachment_access_rights()
```

### 4. Check Specific Employee Access
```python
# Test access to specific employee
employee = env['hr.employee'].browse(employee_id)
try:
    employee.read(['passport_copy'])
    print("Access OK")
except Exception as e:
    print(f"Access denied: {e}")
```

## Common Issues and Solutions

### Issue 1: "Access Denied" Error
**Solution**: Ensure user has `hr.group_hr_user` group

### Issue 2: Can't See Attachments
**Solution**: 
1. Run attachment fix: `env['hr.employee']._fix_all_orphaned_attachments()`
2. Ensure attachments are public: `attachment.write({'public': True})`

### Issue 3: Can't Upload Attachments
**Solution**: Ensure user has write access to `hr.employee` model

### Issue 4: Orphaned Attachments (res_id = 0)
**Solution**: Run the fix wizard or cron job

## Group Assignment Commands

### Add User to HR Group
```python
user = env['res.users'].browse(user_id)
hr_group = env.ref('hr.group_hr_user')
user.write({'groups_id': [(4, hr_group.id)]})
```

### Add User to HR Manager Group
```python
user = env['res.users'].browse(user_id)
hr_manager_group = env.ref('hr.group_hr_manager')
user.write({'groups_id': [(4, hr_manager_group.id)]})
```

### Check User Permissions
```python
user = env['res.users'].browse(user_id)
print("Can read employees:", user.has_group('hr.group_hr_user'))
print("Can write employees:", user.has_group('hr.group_hr_manager'))
```

## Automatic Fix Methods

### 1. Server Action
- Go to Settings > Technical > Actions > Server Actions
- Find "Fix Orphaned Attachments" action
- Run it manually

### 2. Cron Job
- The cron job runs daily automatically
- Check logs for any errors

### 3. Wizard
- Go to any employee record
- Click "Fix Attachments" button in header

### 4. Manual Fix
```python
# In Odoo shell
env['hr.employee']._fix_all_orphaned_attachments()
env['hr.employee']._check_attachment_access_rights()
```

## Testing Access Rights

### Test Script
```python
def test_attachment_access():
    # Test with different user contexts
    users = env['res.users'].search([('active', '=', True)])
    
    for user in users:
        print(f"\nTesting user: {user.name}")
        try:
            with env(user=user.id):
                employees = env['hr.employee'].search([], limit=1)
                if employees:
                    employee = employees[0]
                    result = employee.read(['passport_copy'])
                    print(f"  ✓ Access OK - {len(result[0].get('passport_copy', []))} attachments")
                else:
                    print("  ⚠ No employees found")
        except Exception as e:
            print(f"  ✗ Access denied: {e}")
```

## Recommended Group Structure

### For HR Users:
- `base.group_user`
- `hr.group_hr_user`

### For HR Managers:
- `base.group_user`
- `hr.group_hr_user`
- `hr.group_hr_manager`

### For Administrators:
- `base.group_user`
- `base.group_erp_manager`
- `hr.group_hr_manager`

## Monitoring

### Check Logs
```python
# Check for attachment-related errors
logs = env['ir.logging'].search([
    ('name', 'ilike', 'attachment'),
    ('create_date', '>=', fields.Datetime.now() - timedelta(days=1))
])
for log in logs:
    print(f"{log.create_date}: {log.message}")
```

### Monitor Orphaned Attachments
```python
# Count orphaned attachments
orphaned_count = env['ir.attachment'].search_count([
    ('res_model', '=', 'hr.employee'),
    ('res_id', '=', 0)
])
print(f"Orphaned attachments: {orphaned_count}")
```

This guide should help resolve attachment access issues for all user groups. 