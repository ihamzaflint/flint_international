from odoo import models, fields, api, _, tools
import base64
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import io
import pandas as pd


class ImportApplicants(models.TransientModel):
    _name = 'import.applicants.wizard'
    _description = "Import Functionality Applicants Wizard "
    file_name = fields.Char()
    file = fields.Binary('File')

    def download_excel_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/era_recruitment_opportunity/static/excel/import_applicants_template.xlsx?download=true',
            'target': 'close',
        }

    def action_import_applicants(self):
        # Ensure a file is uploaded
        if not self.file:
            raise ValidationError(_('Please upload a file!'))
        #
        # Retrieve the file name and extension
        file_name = str(self.file_name)
        extension = file_name.split('.')[-1].lower()
        #
        # Check if the file extension is valid
        if extension not in ['xls', 'xlsx']:
            raise ValidationError(_('Please upload only .xls or .xlsx file!'))
        #
        # Decode the binary field to get the file content
        file_content = base64.b64decode(self.file)
        #
        # Use pandas to read the Excel file
        # excel_file = pd.read_excel(io.BytesIO(file_content))
        try:
            excel_file = pd.read_excel(
                io.BytesIO(file_content),
                engine='openpyxl'  # Force openpyxl engine
            )
        except KeyError:
            # Fallback for non-standard Excel files
            excel_file = pd.read_excel(
                io.BytesIO(file_content),
                engine='odf'  # Try LibreOffice engine
            )

        target_columns = [
            "name", "Email", "Contact", "Nationality", "Current Location", "Experience",
            "Qualification", "Current Company", "Position", "Notice Period", "Salary Expectations",
            "Dependants (wife)", "Dependants (kids)", "Profession on Iqama", "Number of Iqama Transfers",
            "Current Salary"
        ]

        # Check if all columns in target_columns exist in the Excel file
        list(excel_file.columns)
        missing = [col for col in target_columns if col not in excel_file.columns]

        # if all(column in list(excel_file.columns) for column in target_columns):
        if not missing:
            # Use the first template's columns
            target_columns = target_columns
            filtered_data = excel_file[target_columns]
            return self.create_job_applicants(filtered_data)
        else:
            raise ValidationError(_('Missing Columns %(columns)s is incorrectly formatted', columns=missing))

    def create_job_applicants(self, filtered_data):
        # Convert the DataFrame to a dictionary
        data_dict = filtered_data.to_dict(orient='records')
        applicants = []
        for entry in data_dict:
            order_vals = self._prepare_job_applicants(entry)
            if order_vals:
                applicants.append(self.env['applicant.line'].create(order_vals))

        orders = [record.id for record in applicants]
        action = {
            'name': 'Applicants Created from Excel',
            'type': 'ir.actions.act_window',
            'res_model': 'applicant.line',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders)],
        }
        return action

    def _prepare_job_applicants(self, entry):
        error = []

        order_data = {
            'recruitment_order_id': self._context.get('default_rec_id'),
            'name': entry['name'],
            # 'alias_name': entry['Email Alias'],
            'email': entry['Email'] if not pd.isna(entry['Email']) else None,
            'phone': entry['Contact'] if not pd.isna(entry['Contact']) else None,
            'nationality': entry['Nationality'] if not pd.isna(entry['Nationality']) else None,
            'current_location': entry['Current Location'] if not pd.isna(entry['Current Location']) else None,
            'experience': entry['Experience'] if not pd.isna(entry['Experience']) else None,
            'qualification': entry['Qualification'] if not pd.isna(entry['Qualification']) else None,
            'current_company': entry['Current Company'] if not pd.isna(entry['Current Company']) else None,
            'position': entry['Position'] if not pd.isna(entry['Position']) else None,
            'notice_period': entry['Notice Period'] if not pd.isna(entry['Notice Period']) else None,
            'salary_expectation': entry['Salary Expectations'] if not pd.isna(entry['Salary Expectations']) else None,
            'profession': entry['Profession on Iqama'] if not pd.isna(entry['Profession on Iqama']) else None,
            'number_iqama': entry['Number of Iqama Transfers'] if not pd.isna(
                entry['Number of Iqama Transfers']) else None,
            'current_salary': entry['Current Salary'] if not pd.isna(entry['Current Salary']) else None,
            'wife': entry['Dependants (wife)'] if not pd.isna(entry['Dependants (wife)']) else None,
            'kids': entry['Dependants (kids)'] if not pd.isna(entry['Dependants (kids)']) else None,
        }
        return order_data
