from odoo import models, fields, api, _, tools
import base64
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import io
import pandas as pd


class ImportJobs(models.TransientModel):
    _name = 'import.jobs.wizard'
    _description = "Import Functionality Jobs Wizard "
    file_name = fields.Char()
    file = fields.Binary('File')

    def download_excel_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/era_recruitment_opportunity/static/excel/import_job_template.xlsx?download=true',
            'target': 'close',
        }

    def action_import_job(self):
        print("Hi")
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
            "name", "Department", "Job Location", "Email Alias", "Employment Type",
            "Recruitment Process", "Client / Project Name", "Position Title",
            "Experience Level", "Preferred Industry", "Target", "Recruiter",
            "Interviewers", "Nationality Requirement", "Salary Range", "Onsite / Remote",
            "Permanent Role / Contract through Flint",
            "Bidding Stage or Live Requirement", "status"
        ]

        # Check if all columns in target_columns exist in the Excel file
        missing = [col for col in target_columns if col not in excel_file.columns]
        # print("Missing columns:", missing)
        print(list(excel_file.columns))
        # if all(column in list(excel_file.columns) for column in target_columns):
        if not missing:
            # Use the first template's columns
            target_columns = target_columns
            filtered_data = excel_file[target_columns]
            #     sale_dis_account = self.env['account.account'].search([('code','=','400001')])
            #
            return self.create_recruitment_order(filtered_data)
        else:
            raise ValidationError(_('Missing Columns %(columns)s is incorrectly formatted', columns=missing))

        # else:
        #     # If the first template's columns are not found, check the second template
        #     report_date = excel_file.iloc[1, 0]
        #
        #     # Extract the substring after "Report Ran At: "
        #     date = report_date.split(":")[-1].strip()
        #     # customer_name = excel_file.iloc[3, 0]
        #     sales_team = excel_file.iloc[5, 0]
        #     # customer_name = customer_name.replace("Dealer: ", "")
        #     table_data = pd.read_excel(
        #         io.BytesIO(file_content),
        #         skiprows=9,  # Skip the first 9 rows
        #         header=0,  # Use row 10 as the header
        #     )
        #     required_columns = ['Total Payment Received', 'Total Tax Paid','Branch Code']
        #     for col in required_columns:
        #         if col not in table_data.columns:
        #             raise ValidationError(_(f'The table must have a "{col}" column!'))
        #
        #     # Get the last value in the "Total Payment Received" column
        #     last_payment_received = table_data['Total Payment Received'].iloc[-1]
        #     discount = table_data['Discounts'].iloc[-1]
        #     customer_name = table_data['Branch Code'].iloc[1]
        #
        #     # Get the last value in the "Total Tax Paid" column
        #     last_tax_paid = table_data['Total Tax Paid'].iloc[-1]
        #     tax_account = self.env['account.account'].search([('code','=','251000')])
        #     payment_account = self.env['account.account'].search([('code','=','213000')])
        #     collection_dis_account = self.env['account.account'].search([('code','=','213010')])
        #     invoice_vals = {
        #         'date': date,
        #         'customer_name': customer_name,
        #         'discount': discount,
        #         'tax_account': tax_account.id if tax_account else None,
        #         'payment_account': payment_account.id if payment_account else None,
        #         'collection_dis_account': collection_dis_account.id if payment_account else None,
        #         'sales_team': sales_team,
        #         'total_amount': last_payment_received,
        #         'tax': last_tax_paid
        #     }
        #     return self.create_invoice_template2(invoice_vals)

    def create_recruitment_order(self, filtered_data):
        # Convert the DataFrame to a dictionary
        data_dict = filtered_data.to_dict(orient='records')
        # Step 2: Populate the defaultdict
        grouped_data = defaultdict(list)
        recruitment_orders = []
        for entry in data_dict:
            order_vals = self._prepare_recruitment_order(entry)
            if order_vals:
                recruitment_orders.append(self.env['recruitment.order'].create(order_vals))

        orders = [record.id for record in recruitment_orders]
        action = {
            'name': 'Jobs Created from Recruitment',
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders)],
        }
        return action

    def _prepare_recruitment_order(self, entry):
        error = []
        # model = self.env['recruitment.order']
        # required_fields = [field_name for field_name, field in model._fields.items() if field.required]
        # print(required_fields)
        recruitment_process = "full_recruitment"
        if entry['Recruitment Process'] == 'Full Recruitment':
            recruitment_process = 'full_recruitment'
        else:
            recruitment_process = 'direct_recruitment'
        department = None
        if not pd.isna(entry['Department']):
            department = self.env['hr.department'].search([('name', '=', entry['Department'])])
            if not department:
                error.append("No department found against the name %s \n" % entry['Department'])

        job_location = None
        if not pd.isna(entry['Job Location']):
            job_location = self.env['res.partner'].search([('name', '=', entry['Job Location'])])
            if not job_location:
                error.append("No Job Location found against the name %s \n" % entry['Job Location'])

        employment_type = None
        if not pd.isna(entry['Employment Type']):
            employment_type = self.env['hr.contract.type'].search([('name', '=', entry['Employment Type'])])
            if not employment_type:
                error.append("No Contract type found against the name %s \n" % entry['Employment Type'])

        # client = None
        # if entry['Client / Project Name']:
        #     employment_type = self.env['res.partner'].search([('name', '=', entry['Client / Project Name'])])
        #     if not employment_type:
        #         error.append("No Client/Project found against the name %s" % entry['Client / Project Name'])

        # client = None
        # if entry['Client / Project Name']:
        #     client = self.env['res.partner'].search([('name', '=', entry['Client / Project Name'])])
        #     if not client:
        #         error.append("No Client/Project found against the name %s \n" % entry['Client / Project Name'])

        recruiter = None
        if not pd.isna(entry['Recruiter']):
            recruiter = self.env['res.users'].search([('name', '=', entry['Recruiter'])])
            if not recruiter:
                error.append("No Recruiter found against the name %s \n" % entry['Recruiter'])

        interviewers = None
        if not pd.isna(entry['Interviewers']):
            partner_names = entry['Interviewers'].split(", ")
            interviewers = self.env['res.users'].search([('name', 'in', partner_names)])
            found_names = set(interviewers.mapped('name'))
            missing_names = [name for name in partner_names if name not in found_names]

            if missing_names:
                error.append(f"The following partner(s) were not found: {', '.join(missing_names)}")
        if error:
            raise ValidationError(error)
        lead_id = self.env['crm.lead'].search([('id', '=', self._context.get("default_lead_id"))])
        order_data = {
            'name': entry['name'],
            # 'alias_name': entry['Email Alias'],
            'recruitment_process': recruitment_process,
            'department_id': department.id if department else None,
            'interviewer_ids': interviewers.ids if interviewers else None,
            'address_id': job_location.id if job_location else None,
            'contract_type_id': employment_type.id if employment_type else None,
            'client_name': lead_id.partner_id.id,
            'position_title': entry['Position Title'] if not pd.isna(entry['Position Title']) else None,
            'experience_level': entry['Experience Level'] if not pd.isna(entry['Experience Level']) else None,
            'onsite_remote': entry['Onsite / Remote'] if not pd.isna(entry['Onsite / Remote']) else None,
            'preferred_industry': entry['Preferred Industry'] if not pd.isna(entry['Preferred Industry']) else None,
            'nationality_requirement': entry['Nationality Requirement'] if not pd.isna(
                entry['Nationality Requirement']) else None,
            'salary_range': entry['Salary Range'] if not pd.isna(entry['Salary Range']) else None,
            'permanent_contract': entry['Permanent Role / Contract through Flint'] if not pd.isna(
                entry['Permanent Role / Contract through Flint']) else None,
            'bidding_stage': entry['Bidding Stage or Live Requirement'] if not pd.isna(
                entry['Bidding Stage or Live Requirement']) else None,
            'user_id': recruiter.id if recruiter else None,
            'no_of_recruitment': entry['Target'] if entry['Target'] else 1,
            # 'VAT': entry['VAT'],
            # 'total_price': entry['Total Price'],
            # 'Quantity': entry['Quantity'],
            # 'Pricing Discounts': entry['Pricing Discounts'],
        }
        return order_data

    def create_invoice_template2(self, filtered_data):
        invoices = []
        vals = self._prepare_entry_template2(filtered_data)
        if vals:
            invoices.append(self.env['account.move'].create(vals))
        invoice_ids = [record.id for record in invoices]
        action = {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
        }
        return action

    def _prepare_entry_template2(self, record):
        partner = None
        formatted_date = None
        if record['customer_name']:
            partner = self.env['res.partner'].search([('name', '=', record['customer_name'])])
        if not partner:
            partner = self.env['res.partner'].create({
                'name': record['customer_name']
            })
        lines = self._prepare_lines_values_template_2(record['tax'], record['total_amount'], record['payment_account'],
                                                      record['tax_account'], record['discount'],
                                                      record['collection_dis_account'])
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%b/%Y']

        # Try parsing with each format
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(record['date'], fmt)
                break
            except ValueError:
                continue

        if parsed_date:
            formatted_date = parsed_date.strftime('%Y-%m-%d')
        return {
            'partner_id': partner.id,
            # 'ref': record['Invoice'],
            'sales_team': record['sales_team'],
            'invoice_date': formatted_date,
            'move_type': 'out_invoice',
            'line_ids': lines
        }

    def _prepare_lines_values_template_2(self, tax, amount, payment_account, tax_account, discount,
                                         collection_dis_account):
        line_ids = []

        line = (0, 0, {
            'name': "Payment",
            'account_id': payment_account,
            'price_unit': amount,
            'quantity': 1
        })
        line_ids.append(line)
        if discount != 0:
            line = (0, 0, {
                'name': "Discount",
                'account_id': collection_dis_account,
                'price_unit': discount,
                'quantity': 1
            })
            line_ids.append(line)
        if tax != 0:
            line = (0, 0, {
                'name': "Tax",
                'account_id': tax_account,
                'price_unit': tax,
                'quantity': 1
            })
            line_ids.append(line)

        return line_ids

    # def _prepare_entry(self,record):
    #     partner = None
    #     if record['Customer'] in ['Walkin Customer' ,'No Customer']:
    #         partner = self.env['res.partner'].search([('name', '=', 'Walkin Customer')])
    #     if not partner:
    #         partner = self.env['res.partner'].create({
    #             'name': record['Customer']
    #         })
    #     lines = self._prepare_lines_values(record['lines'], record['discount_account'])
    #     parsed_date = datetime.strptime(record['Sold On'], '%m/%d/%Y %H:%M:%S')
    #     formatted_date = parsed_date.strftime('%Y-%m-%d')
    #     return {
    #         'partner_id': partner.id,
    #         'ref': record['Invoice'],
    #         'sales_team': record['Sold By'],
    #         'invoice_date': formatted_date,
    #         'move_type': 'out_invoice',
    #         'line_ids': lines
    #     }
    #
    # def _prepare_lines_values(self, lines, discount_account):
    #     line_ids = []
    #     for rec in lines:
    #         tax = None;
    #         if rec['VAT'] != 0:
    #             tax_percentage = (rec['VAT']/rec['total_price']) * 100
    #             tax_percentage = str(float(f"{tax_percentage:.1f}"))+'%'
    #             tax = self.env['account.tax'].search([('name','=',tax_percentage)])
    #         if rec['List Price'] != 0:
    #             line = (0, 0, {
    #                 'name': rec['Label'],
    #                 'price_unit': rec['List Price'],
    #                  'tax_ids': [(6, 0, tax.ids)] if tax else None,
    #                 'quantity': abs(rec['Quantity'])
    #             })
    #             line_ids.append(line)
    #         if rec['Pricing Discounts'] != 0:
    #             line = (0, 0, {
    #                 'name': "Discount for" + rec['Label'],
    #                 'price_unit': -rec['Pricing Discounts'],
    #                 'account_id': discount_account.id,
    #                 'quantity': 1
    #             })
    #             line_ids.append(line)
    #     return line_ids
