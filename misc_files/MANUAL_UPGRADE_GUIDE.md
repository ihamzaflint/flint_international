# Manual Upgrade Guide for scs_operation Module

## Problem Description
The "cursor already closed" error indicates a database connection issue during module upgrade. This typically happens when:
- Database connection is interrupted
- Long-running transactions block the upgrade
- Memory issues cause cursor closure
- Network connectivity problems

## Solutions

### Solution 1: Database Connection Test
First, test your database connection:

```bash
python3 odoo15e_flint/test_db_connection.py
```

This will identify if there are connection issues.

### Solution 2: Manual SQL Cleanup
Connect to your database and run these commands:

```sql
-- 1. Kill any long-running transactions
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query NOT LIKE '%pg_stat_activity%'
AND pid <> pg_backend_pid();

-- 2. Clean up problematic access rights
DELETE FROM ir_model_access 
WHERE group_id IN (
    SELECT ima.group_id 
    FROM ir_model_access ima
    LEFT JOIN res_groups rg ON ima.group_id = rg.id
    WHERE ima.group_id IS NOT NULL 
    AND rg.id IS NULL
);

-- 3. Remove scs_operation access rights that might cause issues
DELETE FROM ir_model_access 
WHERE name LIKE '%scs_operation%' 
AND group_id NOT IN (
    SELECT id FROM res_groups 
    WHERE name IN ('base.group_user', 'hr.group_hr_user', 'hr.group_hr_manager', 'base.group_erp_manager')
);

-- 4. Commit the changes
COMMIT;
```

### Solution 3: Robust Upgrade Script
Use the robust upgrade script that handles connection issues:

```bash
python3 odoo15e_flint/robust_upgrade_script.py
```

### Solution 4: Manual Step-by-Step Upgrade

#### Step 1: Stop Odoo Services
```bash
sudo systemctl stop odoo
# or
sudo service odoo stop
```

#### Step 2: Clean Database Connections
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Kill all connections to your database
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'your_database_name';

# Exit PostgreSQL
\q
```

#### Step 3: Restart PostgreSQL
```bash
sudo systemctl restart postgresql
```

#### Step 4: Start Odoo in Update Mode
```bash
cd /path/to/odoo
python3 odoo-bin -u scs_operation -d your_database_name --stop-after-init
```

#### Step 5: Restart Odoo Services
```bash
sudo systemctl start odoo
```

### Solution 5: Odoo.sh Specific Steps

If you're on Odoo.sh:

1. **Go to your Odoo.sh dashboard**
2. **Navigate to the database**
3. **Go to Settings > Technical > Database Structure**
4. **Run the SQL cleanup commands manually**
5. **Then try the module upgrade again**

### Solution 6: Emergency Recovery

If all else fails:

```bash
# 1. Create a backup
pg_dump your_database_name > backup_before_upgrade.sql

# 2. Drop and recreate the module
python3 odoo-bin -u scs_operation -d your_database_name --uninstall

# 3. Reinstall the module
python3 odoo-bin -i scs_operation -d your_database_name --stop-after-init

# 4. Restore data if needed
psql your_database_name < backup_before_upgrade.sql
```

## Prevention for Future

### 1. Regular Database Maintenance
```sql
-- Run this regularly
VACUUM ANALYZE;
REINDEX DATABASE your_database_name;
```

### 2. Monitor Long-Running Queries
```sql
-- Check for long-running queries
SELECT pid, state, query_start, query 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query NOT LIKE '%pg_stat_activity%';
```

### 3. Set Proper Timeouts
Add to your Odoo configuration:
```ini
[options]
db_maxconn = 64
limit_time_real = 1200
limit_time_cpu = 600
```

## Troubleshooting Checklist

- [ ] Database connection is stable
- [ ] No long-running transactions
- [ ] Sufficient disk space
- [ ] Sufficient memory
- [ ] Network connectivity is stable
- [ ] PostgreSQL is running properly
- [ ] No conflicting module updates

## Emergency Contacts

If the issue persists:
1. Check Odoo.sh support (if applicable)
2. Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`
3. Check Odoo logs: `sudo tail -f /var/log/odoo/odoo-server.log`

## Quick Fix Commands

```bash
# Test connection
python3 odoo15e_flint/test_db_connection.py

# Run robust upgrade
python3 odoo15e_flint/robust_upgrade_script.py

# Manual upgrade with stop-after-init
python3 odoo-bin -u scs_operation -d your_database --stop-after-init
```

This guide should help resolve the cursor error and successfully upgrade the scs_operation module. 