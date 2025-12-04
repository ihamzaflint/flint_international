from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HrTemplateReportsWiz(models.TransientModel):
    _name = 'hr.template.report.wiz'

    @api.depends('leave_from_date', 'leave_to_date')
    def _compute_total_leave_days(self):
        for rec in self:
            total_leave_days = 0
            if rec.leave_to_date and rec.leave_from_date:
                total_leave_days += (rec.leave_to_date - rec.leave_from_date).days
            rec.total_leave_days = total_leave_days + 1

    employee_id = fields.Many2one("hr.employee", string="Employee")
    country_id = fields.Many2one('res.country', "Nationality")
    letter_purpose = fields.Char("Purpose of Letter in Arabic")
    transfer_detail = fields.Char("Transfer Details")
    sequence_no = fields.Char("Sequence No.")
    address_to_whom = fields.Char("Address to Whom")
    address_to_whom_arabic = fields.Char("Address to Whom Arabic")
    contract_no = fields.Char("Contract No")
    contract_validity_date = fields.Date("Contract Validity Date")
    authorised_emp_id = fields.Many2one('hr.employee', 'Authorized')
    commerical_registration_no = fields.Char("Commercial Registration Number")
    company_name = fields.Char("Company Name")
    company_name_arabic = fields.Char("Company Name in Arabic")
    sal_in_words = fields.Char("Total Salary in Words")
    residence_number = fields.Char("(ID) Number")
    work_position = fields.Char("Job Position in Arabic")
    job_contract = fields.Char("Job Contract")
    renew_contract = fields.Char("Re-New Contract")
    contract_expiry_date = fields.Date("Contract Expiry Date")
    article_detail = fields.Char("Article Detail")
    artical_detail_arabic = fields.Char("Article Details in Arabic")
    probation_extend_date = fields.Date("Start Date")
    leave_type = fields.Selection([('annual', 'Annual'),
                                   ('casual', 'Casual'),
                                   ('sick', 'Sick'),
                                   ('emergency', 'Emergency'),
                                   ('compensatory', 'Compensatory')],
                                   "Type of Leave")
    leave_from_date = fields.Date("From Date")
    leave_to_date = fields.Date("End Date")
    leave_remarks = fields.Text("Remarks")
    total_leave_days = fields.Integer("No of Days",
                                      compute="_compute_total_leave_days")
    report_template = fields.Selection([('mobility_entry_permit', 'Mobily Entry Permit'),
                                        ('experience_certificate', 'Experience Certificate'),
                                        ('salary_transfer_from', 'Salary Transfer Form'),
                                        ('liter_embassies', 'Liter for embassies'),
                                        ('salary_introduction_letter', 'Salary Introduction Letter'),
                                        ('disclaimer', 'Disclaimer'),
                                        ('stc_entry_permit', 'STC Entry Permit'),
                                        ('attestation_certificate_1', 'Attestation Certificate 1'),
                                        ('bank_letter_outside_kingdom', 'Bank Letter Outside Kingdom'),
                                        ('registration_crops_of_engineer', 'Registration of SCE'),
                                        ('attestation_certificate_3', 'Attestation Certificate 3'),
                                        ('bank_loan_request', 'Bank Loan Request'),
                                        ('attestation_certificate_2', 'Attestation Certification 2'),
                                        ('sabb_bank_loan', 'SABB Bank Loan'),
                                        ('vacation_job_responsibility', 'Vacation Job Responsibility'),
                                        ('leave_application_form', 'Leave Application Form'),
                                        ('entend_probation_period', 'Extend Probation Period'),
                                        ('warning_letter', 'Warning Letter'),
                                        ('employment_letter', 'Employment Letter')],
                                       string="Template")
    responsibility_ids = fields.One2many("responsibility.details", 'hr_template_id', string="Responsibility Details")
    city_name_english = fields.Char("City Name in English")
    city_name_arabic = fields.Char("City Name in Arabic")
    muqeem_profession = fields.Char("Profession as per Muqeem")
    total_salary = fields.Float("Basic Salary")
    embassy_id = fields.Many2one('embassy.detail', "Embassy")
    artical_detail_ids = fields.One2many('artical.detail', 'hr_templ_id', string="Artical")
    total_gross_sal = fields.Float("Total Gross Salary")
    comm_reg_number_name = fields.Char("Commercial Register Name")
    comm_reg_number_name_arabic = fields.Char("Commercial Register Name Arabic")

    @api.onchange('report_template')
    def onchange_report_template(self):
        for rec in self:
            rec.country_id = rec.leave_from_date = rec.leave_to_date = False
            rec.sequence_no = ''
            rec.transfer_detail = ''
            rec.letter_purpose = ''

    @api.onchange('leave_from_date', 'leave_to_date')
    def onchange_leave_dates(self):
        for rec in self:
            if rec.leave_from_date and rec.leave_to_date:
                if rec.leave_from_date > rec.leave_to_date:
                    raise ValidationError(_(
                "Start Date should be Greater than End Date"))

    @api.onchange('employee_id')
    def onchange_employee(self):
        for rec in self:
            if rec.employee_id:
                rec.residence_number = rec.employee_id.identification_id
                rec.muqeem_profession = rec.employee_id.muqeem_profession
                if rec.employee_id.contract_id:
                    rec.total_salary = rec.employee_id.contract_id.wage
                    rec.total_gross_sal = rec.employee_id.contract_id.total_gross_wage

    def generate_template_report(self):
        data = {}
        if self.report_template == 'mobility_entry_permit':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                return self.env.ref('scs_hr_reports.report_mobily_entry_permit').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                return self.env.ref('scs_hr_reports.report_mobily_entry_permit_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'experience_certificate':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                return self.env.ref('scs_hr_reports.report_experience_certificate').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                return self.env.ref('scs_hr_reports.report_experience_certificate_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'salary_transfer_from':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                self.employee_id.salary_transfer_form_seq += 1
                return self.env.ref('scs_hr_reports.report_salary_transfer_form').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                self.employee_id.salary_transfer_form_seq += 1
                return self.env.ref('scs_hr_reports.report_salary_transfer_female_form').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'liter_embassies':
            self.employee_id.liter_embassies_sequence += 1
            return self.env.ref('scs_hr_reports.report_liter_embassies').report_action(self, data=data)
        if self.report_template == 'salary_introduction_letter':
            self.employee_id.sal_intorduction_letter_seq += 1
            return self.env.ref('scs_hr_reports.report_salary_introduction_letter').report_action(self, data=data)
        if self.report_template == 'disclaimer':
            self.employee_id.disclaimer_sequence += 1
            return self.env.ref('scs_hr_reports.report_disclaimer').report_action(self, data=data)
        if self.report_template == 'stc_entry_permit':
            self.employee_id.stc_entry_permit_sequence += 1
            return self.env.ref('scs_hr_reports.report_stc_entry_permit').report_action(self, data=data)
        if self.report_template == 'attestation_certificate_1':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                self.employee_id.attestation_certificate_1_seq += 1
                return self.env.ref('scs_hr_reports.report_attestation_certificate_1').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                self.employee_id.attestation_certificate_1_seq += 1
                return self.env.ref('scs_hr_reports.report_attestation_certificate_1_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'bank_letter_outside_kingdom':
            return self.env.ref('scs_hr_reports.report_bank_letter_outside_kingdom').report_action(self, data=data)
        if self.report_template == 'registration_crops_of_engineer':
            self.employee_id.crops_eng_registartion_seq += 1
            return self.env.ref('scs_hr_reports.report_crops_engineers_registration').report_action(self, data=data)
        if self.report_template == 'attestation_certificate_3':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                self.employee_id.attestation_certificate_3_seq += 1
                return self.env.ref('scs_hr_reports.report_attestation_certificate_3').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                self.employee_id.attestation_certificate_3_seq += 1
                return self.env.ref('scs_hr_reports.report_attestation_certificate_3_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'bank_loan_request':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                self.employee_id.bank_loan_req_sequence += 1
                return self.env.ref('scs_hr_reports.report_bank_loan_request').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                self.employee_id.bank_loan_req_sequence += 1
                return self.env.ref('scs_hr_reports.report_bank_loan_request_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")
        if self.report_template == 'attestation_certificate_2':
            return self.env.ref('scs_hr_reports.report_attestation_certificate_2').report_action(self, data=data)
        if self.report_template == 'sabb_bank_loan':
            return self.env.ref('scs_hr_reports.report_sabb_bank_loan').report_action(self, data=data)
        if self.report_template == 'vacation_job_responsibility':
            data = self.read([])[0]
            return self.env.ref('scs_hr_reports.report_vacation_job_responsibility').report_action(self, data=data)
        if self.report_template == 'leave_application_form':
            return self.env.ref('scs_hr_reports.report_leave_application_form').report_action(self, data=data)
        if self.report_template == 'entend_probation_period':
            self.employee_id.extend_probation_sequence += 1
            return self.env.ref('scs_hr_reports.report_extend_probation_period').report_action(self, data=data)
        if self.report_template == 'warning_letter':
            self.employee_id.warning_letter_sequence += 1
            return self.env.ref('scs_hr_reports.report_warning_letter').report_action(self, data=data)
        if self.report_template == 'employment_letter':
            if self.employee_id.gender and self.employee_id.gender == 'male':
                self.employee_id.employment_letter_seq += 1
                return self.env.ref('scs_hr_reports.report_employment_letter_male').report_action(self, data=data)
            elif self.employee_id.gender and self.employee_id.gender == 'female':
                self.employee_id.employment_letter_seq += 1
                return self.env.ref('scs_hr_reports.report_employment_letter_female').report_action(self, data=data)
            else:
                raise ValidationError("Please configure Gender for selected employee !")


class ResponsiblilityDetails(models.TransientModel):
    _name = 'responsibility.details'

    name = fields.Char("Name")
    responsibility = fields.Char("Responsibility")
    hr_template_id = fields.Many2one('hr.template.report.wiz', string="Template Detail")
