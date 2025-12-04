# -*- coding: utf-8 -*-
###################################################################################
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Human Resource Reports',
    'version': '1.3',
    'summary': """""",
    'description': """""",
    'category': 'Base',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': "",
    'license': 'AGPL-3',

    'depends': ['hr_recruitment', 'hr_salary_increment'],

    'data': [
        "views/artical_details_view.xml",
        "views/embassy_detail_view.xml",
        "views/hr_job_view.xml",
        "views/hr_applicant_view.xml",
        "views/hr_employee_view.xml",
        "views/res_country_view.xml",
        "security/ir.model.access.csv",
        "reports/job_offer_template.xml",
        "reports/salary_increment_template.xml",
        "reports/agreement_termination_service_template.xml",
        "reports/extending_contract_period_template.xml",
        "reports/renew_contract_template.xml",
        "reports/experience_certificate_template.xml",
        "reports/experience_certificate_female_template.xml",
        "reports/mobily_entry_permit_template.xml",
        "reports/mobily_entry_permit_female_template.xml",
        "reports/salary_transfer_form.xml",
        "reports/salary_transfer_female_form.xml",
        "reports/liter_embassies_template.xml",
        "reports/salary_introduction_letter.xml",
        "reports/disclaimer_template.xml",
        "reports/stc_entry_permit_template.xml",
        "reports/attestation_certificate_1_template.xml",
        "reports/attestation_certificate_1_female_template.xml",
        "reports/bank_letter_outside_kingdom_template.xml",
        "reports/crops_engineer_registration_template.xml",
        "reports/attestation_certificate_3_template.xml",
        "reports/attestation_certificate_3_female_template.xml",
        "reports/bank_loan_request_template.xml",
        "reports/bank_loan_request_female_template.xml",
        "reports/attestation_certificate_2_template.xml",
        "reports/sabb_bank_loan_template.xml",
        "reports/vacation_job_responsibility_template.xml",
        "reports/leave_application_form_template.xml",
        "reports/extend_probation_period_template.xml",
        "reports/warning_letter_template.xml",
        "reports/employment_letter_male.xml",
        "wizard/hr_report_wiz_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
