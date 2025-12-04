# Release Notes - Odoo 15 Enterprise Flint Custom Modules

This document provides an overview of all custom modules in the odoo15e_flint directory.

## Core Modules

### Base Modules
- `base_dynamic_approval` - Dynamic approval system base module
- `base_dynamic_approval_role` - Role-based dynamic approval management
- `base_partner_translatable` - Adds translation capabilities to partner fields
- `itq_core_base` - Core base functionalities for ITQ modules
- `itq_groups_base` - Base module for managing groups and permissions

### Portal & Website
- `itq_portal_base` - Base portal functionalities
- `itq_general_portal_base` - Extended portal features
- `itq_website_base` - Website customizations and features

## Human Resources

### HR Core
- `hr_access_base` - Base HR access control
- `flint_hr_base` - Flint-specific HR base module
- `itq_hr_base` - ITQ HR core functionalities
- `itq_hr_department` - Department management
- `itq_hr_job` - Job position management
- `itq_hr_employee_user_relation` - Employee-user relationship management
- `itq_hr_department_role_access` - Department-based role access control
- `hr_employee_partner_sync` - Employee-partner synchronization
- `itq_employee_role_integration` - Employee role integration system

### HR Documents & Policies
- `hr_employee_checklist` - Employee onboarding checklist
- `itq_hr_document` - HR document management
- `itq_hr_policy` - HR policies management
- `itq_hr_policy_assignation` - Policy assignment system

### Attendance & Time Management
- `itq_attendance_base` - Base attendance module
- `itq_attendance_process` - Attendance processing
- `itq_attendance_punch` - Attendance punch system
- `itq_working_time` - Working time management
- `itq_hr_attendance_policy` - Attendance policies
- `itq_attendance_employee_worksheet` - Employee attendance worksheet
- `itq_attendance_request_correction` - Attendance correction requests
- `itq_attendance_request_correction_portal` - Portal for attendance corrections
- `itq_hr_attendance_contract` - Attendance contract management
- `itq_hr_attendance_dynamic_rest_days` - Dynamic rest days configuration
- `itq_hr_attendance_leaves` - Attendance-leave integration
- `itq_hr_attendance_mandate` - Attendance mandate management
- `itq_hr_attendance_payroll` - Attendance-payroll integration
- `itq_hr_attendance_working_time` - Working time configurations
- `itq_employee_rest_days` - Employee rest days management

### Mandate Management
- `itq_hr_mandate` - HR mandate management
- `itq_hr_mandate_accounting` - Mandate accounting integration
- `itq_hr_mandate_leaves` - Mandate-leave management
- `itq_hr_mandate_project` - Project-related mandates

### Government & Compliance
- `era_muqeem_client` - Muqeem integration client
- `itq_gosi_dashboard` - GOSI dashboard
- `itq_gosi_request` - GOSI request management
- `itq_social_insurance` - Social insurance management
- `itq_social_insurance_accrual` - Social insurance accrual

### Business Travel & Visas
- `itq_business_trip_visit_visa` - Business trip and visit visa management
- `itq_service_visit_visa` - Visit visa service
- `itq_service_visit_visa_accounting` - Visit visa accounting
- `itq_service_visit_visa_portal` - Visit visa portal interface

### Residence & Sponsorship
- `itq_residence_permit_issuance` - Residence permit management
- `itq_residence_permit_issuance_accounting` - Residence permit accounting
- `itq_sponsorship_transfer` - Sponsorship transfer management
- `itq_sponsorship_transfer_accounting` - Sponsorship transfer accounting
- `itq_sponsorship_transfer_portal` - Portal for sponsorship transfers
- `itq_change_residence_profession_portal` - Residence profession change portal

### Employee Services
- `itq_employee_payment_request` - Employee payment requests
- `itq_employee_sponsor_salary_payment` - Sponsor salary payments
- `itq_work_replacement_request` - Work replacement management
- `itq_work_replacement_portal` - Portal for work replacements
- `itq_compensation_request` - Compensation request management

### Leave Management
- `itq_hr_leave` - Leave management system
- `itq_timeoff_portal` - Portal interface for time off requests
- `itq_hr_leave_termination` - Leave termination handling

### Payroll & Benefits
- `payroll_base` - Base payroll system
- `payroll_benefit` - Employee benefits management
- `payroll_base` - ITQ payroll system
- `itq_hr_benefits` - Benefits management
- `itq_salary_schema` - Salary structure schema
- `itq_salary_structure_base` - Base salary structure

### Loans & Financial
- `itq_loans` - Loan management system
- `itq_loans_portal` - Portal interface for loans
- `itq_eos_loan` - End of service loans
- `itq_cheque_management` - Cheque management system
- `itq_petty_cash_management` - Petty cash management

### End of Service
- `itq_end_of_service` - End of service management
- `itq_end_of_service_accounting` - EOS accounting integration
- `itq_end_of_service_portal` - Portal interface for EOS
- `itq_eos_provision` - EOS provision management

### Recruitment
- `flint_recruitment` - Recruitment management
- `itq_hr_applicant` - Applicant management
- `itq_recruitment_plan` - Recruitment planning

## Finance & Accounting

### Accounting
- `ft_account_base` - Base accounting customizations
- `itq_account_access_base` - Account access control
- `itq_account_accrual` - Accrual management

### Accounting Extensions
- `itq_department_analytic_integration` - Department analytic account integration
- `itq_service_accounting_base` - Service accounting base
- `itq_cheque_petty_cash_management` - Integrated cheque and petty cash management

### Treasury
- `itq_treasury_payment_request` - Treasury payment requests
- `treasury_payment_request_base` - Base treasury payment system
- `treasury_payment_payroll` - Payroll payment integration

### Contract Management
- `contract_base` - Base contract management
- `contract_benefit` - Contract benefits management
- `hr_contract_template` - HR contract templates

### Period Management
- `itq_period` - Period management system
- `itq_vacation_provision` - Vacation provision management
- `itq_accrual_rules` - Accrual rules management
- `itq_employee_accrual` - Employee accrual management

## Project & Document Management

### Document Management
- `itq_documents` - Document management system
- `itq_hr_attachment` - HR attachment management
- `itq_company_stamps` - Company stamps management

### Project Extensions
- `itq_boq_items` - Bill of Quantities items
- `itq_eos_provision_project` - EOS provision project integration
- `itq_loan_project` - Loan project integration

### Project Management
- `itq_project_base` - Base project management
- `itq_hr_project` - HR project integration
- `itq_working_time_project_integration` - Working time project integration

## Service Management
- `itq_service_base` - Base service management
- `itq_service_license_renewal` - License renewal service
- `itq_service_visit_visa` - Visit visa service management

## Helpdesk
- `flint_helpdesk` - Helpdesk management system
- `flint_helpdesk_portal` - Portal interface for helpdesk
- `helpdesk_portal` - Additional helpdesk portal features

## Reports & Analytics
- `scs_hr_reports` - HR reporting suite
- `itq_end_of_service_reports` - End of service reports
- `hr_printout_group` - HR printout grouping

## Integration & Utilities
- `itq_abstract_lookup_integration` - Abstract lookup integration
- `itq_archive_o2m` - One2many archive functionality
- `itq_partner_type` - Partner type management
- `itq_res_partner_base` - Partner base customizations
- `alert_wizard` - Alert wizard functionality
- `hijri_date_util` - Hijri date utilities
- `numeric_negative_block` - Negative number handling
- `itq_auto_oe_chatter` - Automated chatter messages

---

Note: This release note includes the main custom modules and their primary functions. Each module may have additional features and dependencies not listed here. For detailed documentation of each module, please refer to their respective README files and technical documentation.
