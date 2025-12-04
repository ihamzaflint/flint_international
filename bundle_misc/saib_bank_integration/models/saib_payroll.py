from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import re
import datetime
import logging
import traceback
import base64
import json
import gzip
import io
import random
import string
import pytz
import xlsxwriter
import os

# Try to import unidecode for Arabic transliteration
try:
    from unidecode import unidecode
except ImportError:
    _logger = logging.getLogger(__name__)
    _logger.warning(
        "The unidecode library is not installed. "
        "Arabic name transliteration will not be available. "
        "Install it with: pip install unidecode"
    )
    # Fallback no-op function
    def unidecode(text):
        return text

_logger = logging.getLogger(__name__)

class SaibPayroll(models.Model):
    _name = 'saib.payroll'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'SAIB Payroll Processing'
    
    name = fields.Char('Reference', required=True, readonly=True, default='New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Bank'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed')
    ], default='draft', tracking=True)
    payroll_date = fields.Date('Payroll Date', required=True)
    mol_establishment_id = fields.Char('MOL Establishment ID', required=True)
    total_amount = fields.Monetary('Total Amount', compute='_compute_total_amount')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    line_ids = fields.One2many('saib.payroll.line', 'payroll_id', string='Payroll Lines')
    employee_count = fields.Integer(compute='_compute_employee_count')
    bank_account_id = fields.Many2one('res.partner.bank', 'Company Bank Account', required=True)
    payment_method = fields.Selection([
        ('wps', 'WPS System'),
        ('direct', 'Direct Transfer')
    ], string='Payment Method', default='wps', required=True)
    wps_reference = fields.Char('WPS Reference')
    wps_status = fields.Char('WPS Status')
    response_data = fields.Text('Bank Response', readonly=True)
    api_reference = fields.Char('API Reference Number', readonly=True, copy=False, 
                              help='Unique reference number used for API calls to prevent duplicates')
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch', readonly=True, 
                                    help='Related payslip batch that generated this SAIB payroll')
    inquiry_response = fields.Text('Inquiry Response', readonly=True)
    excel_file = fields.Binary('Excel File', readonly=True)
    excel_filename = fields.Char('Excel Filename', readonly=True)
    
    
    # [sanjay-techvoot] Auto-generate sequence for multiple record creation.
    # Ensures each new payroll gets a unique name if default provided.
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('saib.payroll') or 'New'
        return super().create(vals_list)
    
    # [sanjay-techvoot] Compute number of payroll lines (employees) for this payroll.
    # Stores count in employee_count.
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(record.line_ids)

    # [sanjay-techvoot] Open a view listing employees included in this payroll.
    # Returns an Odoo window action for hr.employee filtered by payroll lines.
    def action_view_employees(self):
        self.ensure_one()
        return {
            'name': 'Employees',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.line_ids.mapped('employee_id').ids)]
        }

    # [sanjay-techvoot] Compute total payroll amount from payroll lines.
    # Rounds to 2 decimals to match bank transaction precision.
    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        """Compute total amount for the current payment batch only.
        For split payments (regular vs adjustment), this should only include
        the amounts in the current batch to match SAIB's transaction validation.
        """
        for record in self:
            # Calculate total from current payroll lines only
            # Do not include adjustment amounts as they will be in a separate batch
            total = sum(float(line.amount) for line in record.line_ids)
            # Round to 2 decimal places to match transaction amounts
            record.total_amount = round(total, 2)
    
    # [sanjay-techvoot] Prepare payroll payload matching SAIB B2B API requirements.
    # Builds employee entries, validates fields, compresses details before return.
    def _prepare_payroll_data(self):
        """Prepare payroll data in the format required by SAIB B2B API"""
        self.ensure_one()
        
        # Get config parameters
        config = self.env['ir.config_parameter'].sudo()
        
        # Get current time in Riyadh timezone
        current_riyadh = self._get_riyadh_date()
        current_time = current_riyadh.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Calculate total amount
        total_amount = sum(line.amount for line in self.line_ids)
        sequence_base = current_riyadh.strftime("%Y%m%d%H%M")
        
        # Prepare employee data
        employees_data = []
        for idx, line in enumerate(self.line_ids, 1):
            employee = line.employee_id
            sequence_num = f"{sequence_base}{str(idx).zfill(4)}"
            # First try to get from line.bank_account, then from employee's bank account
            account_number = None
            if line.bank_account:
                account_number = line.bank_account
            elif employee.bank_account_id and employee.bank_account_id.acc_number:
                account_number = employee.bank_account_id.acc_number
            
            bank_account = self._clean_iban(account_number)
            employee_name = self._clean_customer_name(employee.name)
            # Format the amount with decimal point as decimal separator
            amount_str = self._format_amount(line.amount)
            
            # Get deductions amount (absolute value)
            deductions = self._get_employee_deductions(line.employee_id, self.payslip_run_id)
            deductions_str = self._format_amount(deductions)  # This will make it positive
            
            # Get regular allowances
            regular_allowances = self._get_employee_regular_allowances(line.employee_id, self.payslip_run_id)
            regular_allowances_str = self._format_amount(regular_allowances)
            is_adjustment = '/Adjustments' in self.name
            if is_adjustment:
                # For adjustments: Only include the adjustment amount
                basic_salary = 0
                housing_allowance = 0
                other_earning = float(amount_str)  # Full amount goes to other earnings
                deduction = 0
            else:
                # For regular payroll: Use standard values minus adjustments
                basic_salary = float(self._format_amount(employee.contract_id.wage))
                housing_allowance = float(self._format_amount(employee.contract_id.l10n_sa_housing_allowance or 0))
                deduction = float(deductions_str)
                
                # Calculate other earnings as the remainder to match line amount
                other_earning = float(amount_str) + deduction - basic_salary - housing_allowance
                if other_earning < 0:
                    # If other earnings would be negative, adjust basic salary instead
                    basic_salary = float(amount_str) + deduction - housing_allowance
                    other_earning = 0
            
            # Calculate total value amount
            value_amount = basic_salary + housing_allowance + other_earning - deduction

            if not bank_account:
                raise UserError(f"Employee {employee.name} has a missing or invalid bank account number. Please add a valid bank account for this employee.")
                
            # Clean and validate customer name
            customer_name = self._clean_customer_name(employee.name)
            
            # Prepare employee entry
            employee_entry = {
                "Sender": config.get_param('saib_bank_integration.company_code'),
                "SequenceNum": sequence_num,
                "TransactionReference": sequence_num,
                "ValueDate": self.payroll_date.strftime("%Y-%m-%d"),
                "ValueCurrencyCode": self.currency_id.name,
                "SenderBankCode": "SIBCSARI",
                "BenCustomerName": employee_name,
                "BenCustomerAddrLine1": "".join(employee.address_id.street.split()) if employee.address_id and isinstance(employee.address_id.street, str) else "",
                "BenCustomerAddrLine2": "".join(employee.address_id.street2.split()) if employee.address_id and isinstance(employee.address_id.street2, str) else "",
                "BenCustomerAddrLine3": "".join(employee.address_id.city.split()) if employee.address_id and isinstance(employee.address_id.city, str) else "",
                "PaymentDetailMsg1": "EASYPAY-PAYROLL",
                "PaymentDetailMsg2": None,
                "PaymentDetailMsg3": None,
                "DetailCharge": None,
                "NationalId": employee.visa_no or employee.identification_id or employee.passport_id,
                "BenAccountNumber": self._clean_iban(employee.bank_account_id.acc_number),
                "BenBank": employee.bank_account_id.bank_id.bic,
                "ValueAmount": self._format_amount(line.amount),
                "PaymentDetails": f"Salary for {customer_name}",
                "BasicSalary": self._format_amount(basic_salary),
                "HousingAllowance": self._format_amount(housing_allowance),
                "OtherEarning": self._format_amount(other_earning),
                "Deduction": self._format_amount(deduction),

            }
            
            # Add to employees data
            employees_data.append(employee_entry)
        
        # Prepare final payload
        bank_account = self.bank_account_id
        if not bank_account or not bank_account.acc_number:
            raise UserError("Please configure a valid bank account for the payroll")
            
        # Clean company bank account number
        company_account = self._clean_iban(bank_account.acc_number)
        if not company_account:
            raise UserError("Company bank account number is invalid")
            
        # Get the sender code from configuration - use the same parameter as government payments
        sender = config.get_param('saib_bank_integration.company_code')
        if not sender:
            sender = 'FLINTID'  
            _logger.warning("Using default company code 'FLINTID' as it's not configured in settings")
        
        # Generate a unique reference for this API call if not already set
        if not self.api_reference:
            # Create a unique reference with timestamp and random suffix
            timestamp = current_riyadh.strftime("%Y%m%d%H%M%S")
            random_suffix = ''.join(random.choices('0123456789', k=4))
            self.api_reference = f"PR{timestamp}{random_suffix}"
            
        # Ensure the reference is alphanumeric only and within length limits
        api_ref = re.sub(r'[^a-zA-Z0-9]', '', self.api_reference)[:16]
            
        # Clean company name
        company_name = self._clean_customer_name(self.company_id.name)
        
        payload = {
            "Sender": sender,
            "Receiver": "SIBC",
            "RequestDate": current_time,
            "PayrollMessageRef": api_ref,
            "WpsMessage": "true" if self.payment_method == 'wps' else "false",
            "MolEstablishmentID": self.mol_establishment_id,
            "PayrollTransactionCount": str(len(self.line_ids)),
            "PayrollTransactionAmount": self._format_amount(total_amount),
            "DebtorAccount": {
                "AccountNumber": company_account,
                "DebtorName": company_name,
                "AddressDetails": [
                    self._remove_arabic_chars(self.company_id.street or ""),
                    self._remove_arabic_chars(self.company_id.city or ""),
                    self._remove_arabic_chars(self.company_id.country_id.name if self.company_id.country_id else "")
                ]
            },
            "PayrollDetails": employees_data  
        }
        
        # Log the request data for debugging with more details
        _logger.info(f"Preparing payroll data for SAIB API")
        _logger.info(f"Sender: {payload.get('Sender')}")
        _logger.info(f"PayrollMessageRef: {payload.get('PayrollMessageRef')}")
        _logger.info(f"MolEstablishmentID: {payload.get('MolEstablishmentID')}")
        _logger.info(f"PayrollTransactionCount: {payload.get('PayrollTransactionCount')}")
        _logger.info(f"PayrollTransactionAmount: {payload.get('PayrollTransactionAmount')}")
        _logger.info(f"RequestDate: {payload.get('RequestDate')} (Riyadh time)")
        
        # Validate required fields
        if not payload.get('Sender'):
            raise UserError('Sender cannot be empty in SAIB API request')
        if not payload.get('PayrollMessageRef'):
            raise UserError('PayrollMessageRef cannot be empty in SAIB API request')
        if not payload.get('MolEstablishmentID'):
            raise UserError('MolEstablishmentID cannot be empty in SAIB API request')
        
        # Verify transaction amounts match before compressing
        self._verify_transaction_amounts(payload)
        
        # Now update with compressed data
        compressed_data = self._compress_payroll_data(employees_data)
        payload['PayrollDetails'] = compressed_data
        
        return payload
    
    # [sanjay-techvoot] Validate that the request date is the current Riyadh date.
    # Raises UserError when dates mismatch or format invalid.
    def _validate_request_date(self, request_date_str):
        """Validate that request date is current date in Riyadh timezone"""
        try:
            # Parse the request date
            request_date = datetime.datetime.strptime(request_date_str, "%Y-%m-%dT%H:%M:%S")
            
            # Get current time in Riyadh timezone
            current_utc = fields.Datetime.now()
            riyadh_tz = pytz.timezone('Asia/Riyadh')
            current_riyadh = pytz.utc.localize(current_utc).astimezone(riyadh_tz)
            
            # Compare dates (ignoring time)
            if request_date.date() != current_riyadh.date():
                raise UserError(
                    f"Request date must be current date in Riyadh timezone.\n"
                    f"Request date: {request_date.date()}\n"
                    f"Current date (Riyadh): {current_riyadh.date()}"
                )
            
            return True
        except ValueError as e:
            raise UserError(f"Invalid request date format: {str(e)}")
            
    # [sanjay-techvoot] Ensure declared total matches the sum of payroll ValueAmount fields.
    # Raises UserError on mismatch or invalid data.
    def _verify_transaction_amounts(self, payload):
        """Verify that PayrollTransactionAmount matches sum of all ValueAmount fields"""
        try:
            # Get total transaction amount from payload
            total_declared = float(payload['PayrollTransactionAmount'])
            
            # Calculate sum of individual transactions
            total_actual = 0.0
            for entry in payload.get('PayrollDetails', []):
                if isinstance(entry, dict) and 'ValueAmount' in entry:
                    total_actual += float(entry['ValueAmount'])
            
            # Round both amounts to 2 decimal places
            total_declared = round(total_declared, 2)
            total_actual = round(total_actual, 2)
            
            if total_declared != total_actual:
                raise UserError(
                    f"Transaction amount mismatch: PayrollTransactionAmount ({total_declared}) "
                    f"does not match sum of ValueAmount fields ({total_actual})"
                )
            
            return True
        except (ValueError, TypeError) as e:
            raise UserError(f"Error verifying transaction amounts: {str(e)}")
    
    # [sanjay-techvoot] Format numeric amount to SAIB's required string (2 decimals, positive).
    # Returns string like "123.45".
    def _format_amount(self, amount):
        """Format amount according to SAIB bank requirements:
            - Use decimal point (not comma) as decimal separator
            - Always show 2 decimal places
            - Properly round to avoid floating point precision issues
            - Convert negative amounts to positive for deductions
        """
        try:
            # Convert to float and take absolute value
            amount = abs(float(amount))
            # Round to 2 decimal places and format
            return "{:.2f}".format(amount)
        except (ValueError, TypeError):
            return "0.00"
    
    # [sanjay-techvoot] Remove Arabic characters from a text string.
    # Returns cleaned string or empty string if input falsy.
    def _remove_arabic_chars(self, text):
        if not text:
            return ""
        # Remove any character in the Arabic unicode range
        return re.sub(r'[\u0600-\u06FF]+', '', text).strip()

    # [sanjay-techvoot] Generate a short unique PayrollMessageRef (<=16 chars).
    # Uses date and random chars to reduce collision risk.
    def _generate_payroll_message_ref(self):
        """Generate a random PayrollMessageRef for SAIB Bank API - max 16 characters"""
        # Generate a random string of 6 uppercase letters and numbers
        chars = string.ascii_uppercase + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(6))
        
        # Add prefix with shorter timestamp to ensure uniqueness while staying within 16 chars
        # Format: SB + YYMMDD + 6 random chars = 2 + 6 + 6 = 14 chars
        timestamp = datetime.datetime.now().strftime('%y%m%d')
        return f"SB{timestamp}{random_str}"
    
    # [sanjay-techvoot] Sum allowances for an employee from payslip run (excludes certain categories).
    # Returns formatted amount string.
    def _get_employee_allowances(self, employee, payslip_run):
        """Calculate the sum of allowances for an employee from a payslip run"""
        if not payslip_run:
            return "0.00"
            
        payslip = payslip_run.slip_ids.filtered(lambda slip: slip.employee_id == employee)
        if not payslip:
            return "0.00"
            
        # Get allowance categories excluding BASIC and HRA (handled separately)
        allowance_categories = ['ALW', 'TRANS', 'FOOD', 'OTH']
        allowances = payslip.line_ids.filtered(lambda line: line.category_id.code in allowance_categories)
        
        # For regular payroll: exclude adjustment allowances
        total_allowances = sum(allowances.filtered(lambda line: 
            not (hasattr(line, 'other_hr_payslip_ids') and 
                 line.other_hr_payslip_ids.filtered(lambda adj: adj.operation_type == 'allowance' and adj.state == 'done'))
        ).mapped('total'))
        
        return self._format_amount(total_allowances)
    
    # [sanjay-techvoot] Sum adjustment allowances from other.hr.payslip model for an employee.
    # Returns formatted amount string or "0.00" on error.
    def _get_employee_adjustment_allowances(self, employee, payslip_run):
        """Calculate the sum of allowances from other.hr.payslip for an employee"""
        if not payslip_run:
            return "0.00"
            
        payslip = payslip_run.slip_ids.filtered(lambda slip: slip.employee_id == employee)
        if not payslip:
            return "0.00"
        
        # Check if other.hr.payslip model exists
        try:
            # Get all adjustments for this payslip by going through payslip lines
            other_payslips = self.env['other.hr.payslip'].sudo()
            total_adjustments = 0
            
            # Payslip lines might contain references to other.hr.payslip records
            for line in payslip.line_ids:
                if not hasattr(line, 'other_hr_payslip_ids'):
                    continue
                    
                adjustment_lines = line.other_hr_payslip_ids.filtered(
                    lambda adj: adj.operation_type == 'allowance' and adj.state == 'done'
                )
                total_adjustments += sum(adjustment_lines.mapped('amount'))
                
            # Return the amount properly rounded and formatted
            return self._format_amount(total_adjustments)
        except Exception as e:
            _logger.error(f"Error accessing other.hr.payslip model: {e}")
            return "0.00"
    
    # [sanjay-techvoot] Compute regular allowances (or adjustment-only) for an employee.
    # Returns formatted amount string.
    def _get_employee_regular_allowances(self, employee, payslip_run):
        """Calculate the regular allowances excluding the ones from other.hr.payslip"""
        if not payslip_run:
            return "0.00"
            
        payslip = payslip_run.slip_ids.filtered(lambda slip: slip.employee_id == employee)
        if not payslip:
            return "0.00"
            
        # Get allowance categories excluding BASIC and HRA (handled separately)
        allowance_categories = ['ALW', 'TRANS', 'FOOD', 'OTH']
        allowances = payslip.line_ids.filtered(lambda line: line.category_id.code in allowance_categories)
        
        # For regular payroll: exclude adjustment allowances
        # For adjustment payroll: only include adjustment allowances
        is_adjustment = '/Adjustments' in self.name
        if is_adjustment:
            # Only include adjustment allowances
            total_allowances = sum(allowances.filtered(lambda line: 
                hasattr(line, 'other_hr_payslip_ids') and 
                line.other_hr_payslip_ids.filtered(lambda adj: adj.operation_type == 'allowance' and adj.state == 'done')
            ).mapped('total'))
        else:
            # Include all regular allowances except housing (handled separately)
            total_allowances = sum(allowances.filtered(lambda line: 
                not (hasattr(line, 'other_hr_payslip_ids') and 
                     line.other_hr_payslip_ids.filtered(lambda adj: adj.operation_type == 'allowance' and adj.state == 'done'))
            ).mapped('total'))
        
        # Return the amount properly rounded and formatted
        return self._format_amount(total_allowances)
    
    # [sanjay-techvoot] Sum deduction lines for an employee from payslip run.
    # Returns formatted amount string.
    def _get_employee_deductions(self, employee, payslip_run):
        """Calculate the sum of deductions for an employee from a payslip run"""
        if not payslip_run:
            return "0.00"
            
        payslip = payslip_run.slip_ids.filtered(lambda slip: slip.employee_id == employee)
        if not payslip:
            return "0.00"
            
        deductions = payslip.line_ids.filtered(lambda line: line.category_id.code == 'DED')
        total_deductions = sum(deductions.mapped('total'))
        
        # Return the amount properly rounded and formatted
        return self._format_amount(total_deductions)
    
    # [sanjay-techvoot] Convert dates to Riyadh timezone; default returns current Riyadh datetime.
    # Handles naive datetimes and date objects.
    def _get_riyadh_date(self, date_obj=None):
        """Convert a date/datetime to Riyadh timezone. If no date provided, returns current Riyadh date."""
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        
        if date_obj is None:
            # Get current time in Riyadh timezone
            current_utc = fields.Datetime.now()
            current_riyadh = pytz.utc.localize(current_utc).astimezone(riyadh_tz)
            return current_riyadh
        
        # If it's a date object, convert to datetime at start of day
        if isinstance(date_obj, datetime.date):
            date_obj = datetime.datetime.combine(date_obj, datetime.time.min)
        
        # If it's naive (no timezone), assume it's UTC
        if not hasattr(date_obj, 'tzinfo') or date_obj.tzinfo is None:
            date_obj = pytz.utc.localize(date_obj)
            
        # Convert to Riyadh timezone
        return date_obj.astimezone(riyadh_tz)

    # [sanjay-techvoot] Determine adjustment payment date (from payslip_run or +2 days Riyadh).
    # Returns a date object.
    def _get_adjustment_date(self):
        """Calculate the adjustment payment date in Riyadh timezone.
        - If adjustment_effective_date is set in payslip_run, use that
        - Otherwise, use current Riyadh date + 2 days
        """
        if self.payslip_run_id and self.payslip_run_id.adjustment_effective_date:
            # Convert the adjustment date to Riyadh timezone
            adjustment_date = self._get_riyadh_date(self.payslip_run_id.adjustment_effective_date)
            return adjustment_date.date()
        else:
            # Get current Riyadh date and add 2 days
            current_riyadh = self._get_riyadh_date()
            return (current_riyadh + datetime.timedelta(days=2)).date()

    # [sanjay-techvoot] Compress payroll details with gzip and return base64 string.
    # Used to send compressed payload to SAIB API.
    def _compress_payroll_data(self, payroll_data):
        """Compress payroll data as required by the API"""
        try:
            # Convert to JSON string
            json_data = json.dumps(payroll_data)
            
            # Use gzip for compression instead of zlib directly
            import gzip
            import io
            
            # Create a BytesIO buffer to hold the gzipped data
            buffer = io.BytesIO()
            
            # Create a GzipFile that writes to the buffer
            with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=9) as f:
                f.write(json_data.encode('utf-8'))
            
            # Get the compressed data from the buffer
            compressed = buffer.getvalue()
            
            # Convert to base64 encoding
            base64_data = base64.b64encode(compressed)
            
            return base64_data.decode('utf-8')
        except Exception as e:
            _logger.error(f"Error compressing payroll data: {str(e)}")
            raise UserError(f"Error preparing payroll data: {str(e)}")
    
    # [sanjay-techvoot] Decompress base64+gzip payroll data returned by SAIB.
    # Returns parsed JSON or informative error structure.
    def _decompress_payroll_data(self, compressed_data):
        """Decompress payroll data from the API response"""
        try:
            # Decode base64
            decoded_data = base64.b64decode(compressed_data)
            
            # Use gzip for decompression
            import gzip
            import io
            
            # Create a BytesIO buffer with the compressed data
            buffer = io.BytesIO(decoded_data)
            
            # Create a GzipFile to read from the buffer
            with gzip.GzipFile(fileobj=buffer, mode='rb') as f:
                decompressed_data = f.read().decode('utf-8')
            
            # Log the raw decompressed data for debugging
            _logger.info(f"Raw decompressed data: {decompressed_data}")
            
            # Handle empty or invalid JSON
            if not decompressed_data or decompressed_data.isspace():
                return {"message": "Empty response from bank"}
                
            # Parse the JSON data
            try:
                return json.loads(decompressed_data)
            except json.JSONDecodeError as json_err:
                # If JSON parsing fails, return the raw string for inspection
                _logger.error(f"JSON decode error: {str(json_err)}")
                return {"raw_data": decompressed_data, "error": f"Invalid JSON format: {str(json_err)}"}
        except Exception as e:
            _logger.error(f"Error decompressing payroll data: {str(e)}")
            return {"error": f"Failed to decompress data: {str(e)}"}
    
    # [sanjay-techvoot] Send payroll (regular and adjustments split) to SAIB and handle responses.
    # Manages state transitions, creates adjustment payrolls, and returns notification action.
    def action_send_to_bank(self):
        """Send payroll data to SAIB bank"""
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError('Cannot send empty payroll to bank. Please add payroll lines first.')
            
        try:
            # Get API service
            api_service = self.env['saib.api']
            
            # Check if this record was previously sent and reset to draft
            # This is determined by checking if api_reference exists, which means it was sent before
            was_reset_to_draft = bool(self.api_reference) and self.state == 'draft'
            
            # If record was reset to draft, process it alone without creating additional records
            if was_reset_to_draft:
                _logger.info(f"Processing reset record alone with existing reference: {self.api_reference}")
                
                # Reuse the existing reference if available, otherwise generate a new one
                message_ref = self.api_reference or self._generate_payroll_message_ref()
                
                # Generate the payroll data without splitting
                payroll_data = self._prepare_payroll_data()
                payroll_data['PayrollMessageRef'] = message_ref
                
                # Set variables for the rest of the function
                regular_payroll = self
                regular_payroll_data = payroll_data
                regular_message_ref = message_ref
                
                # No adjustments when processing a reset record
                adjustment_payroll = None
                adjustment_payroll_data = None
                
            else:
                # Standard processing with split payments
                # Split payroll into regular and adjustments
                adjustment_payroll_data = None
                adjustment_payroll = None
                
                # This is now the "/Regular" payroll from action_create_saib_payroll
                regular_payroll = self
                regular_payroll_data = None
                
                # Store original payroll lines
                original_payroll_lines = self.line_ids
                
                # Process payroll lines to identify adjustments
                employees_with_adjustments = []
                
                # Update existing payroll lines to exclude adjustment amounts
                for line in original_payroll_lines:
                    employee = line.employee_id
                    
                    # Get the original full amount
                    original_amount = line.amount
                    
                    # Calculate adjustment amount
                    adjustment_amount = self._get_employee_adjustment_allowances(employee, self.payslip_run_id)
                    
                    # Calculate regular amount as the whole amount minus the adjustment amount
                    regular_amount = float(original_amount) - float(adjustment_amount)
                    
                    # Track employees with adjustments
                    if float(adjustment_amount) > 0.0:
                        employees_with_adjustments.append(employee.id)
                    
                    # Update the line amount to remove the adjustment amount
                    if float(regular_amount) != float(original_amount):
                        line.write({'amount': regular_amount})
                
                # Generate the regular payroll data
                regular_payroll_data = self._prepare_payroll_data()
                
                # Generate random PayrollMessageRef for regular transaction
                regular_message_ref = self._generate_payroll_message_ref()
                regular_payroll_data['PayrollMessageRef'] = regular_message_ref
                
                # Find employees with adjustment allowances
                if employees_with_adjustments:
                    # Calculate adjustment date in Riyadh timezone
                    adjustment_date = self._get_adjustment_date()
                    
                    adjustment_payroll = self.copy({
                        'name': f"{self.payslip_run_id.name}/Adjustments",
                        'line_ids': False,  
                        'api_reference': False,     
                        'payroll_date': adjustment_date,  
                    })
                    
                    # Create lines only for employees with adjustments
                    for employee_id in employees_with_adjustments:
                        employee = self.env['hr.employee'].browse(employee_id)
                        line = self.line_ids.filtered(lambda l: l.employee_id.id == employee_id)
                        if line:
                            adjustment_amount = float(self._get_employee_adjustment_allowances(employee, self.payslip_run_id))
                            if adjustment_amount > 0:
                                adjustment_payroll.write({
                                    'line_ids': [(0, 0, {
                                        'employee_id': employee.id,
                                        'amount': adjustment_amount,
                                        'currency_id': self.currency_id.id,
                                        'bank_account': employee.bank_account_id.acc_number or '',
                                    })]
                                })
                
                    # Generate the adjustment payroll data
                    adjustment_payroll_data = adjustment_payroll._prepare_payroll_data()
                    
                    # Generate random PayrollMessageRef for adjustment transaction
                    adjustment_message_ref = adjustment_payroll._generate_payroll_message_ref()
                    adjustment_payroll_data['PayrollMessageRef'] = adjustment_message_ref
                else:
                    # No actual adjustments, delete the record
                    adjustment_payroll = None
                    adjustment_payroll_data = None
            
            # Track overall success
            overall_success = False
            responses = []
            
            # Send regular payroll to bank
            api_result = None
            try:
                _logger.info(f"Sending regular payroll to bank with MessageRef: {regular_message_ref}")
                api_result = api_service._make_request(
                    'POST', 
                    '/b2b-rest-payroll-service/b2b/payroll/payment', 
                    regular_payroll_data
                )
                self.write({
                    'response_data': json.dumps(api_result, indent=2) if api_result else '',
                    'state': 'sent',
                    'api_reference': regular_message_ref,
                    'wps_reference': regular_message_ref,
                    'wps_status': 'Sent',
                })
                overall_success = True
                responses.append({
                    'type': 'Regular Payroll',
                    'status': 'Success',
                    'message': f'Reference: {regular_message_ref}'
                })
            except Exception as e:
                error_message = str(e)
                tb = traceback.format_exc()
                _logger.error(f"Error sending regular payroll to bank: {error_message}\n{tb}")
                self.write({
                    'response_data': error_message,
                    'state': 'failed'
                })
                responses.append({
                    'type': 'Regular Payroll',
                    'status': 'Failed',
                    'message': error_message
                })
            
            # Send adjustment payroll to bank if exists
            if adjustment_payroll and adjustment_payroll_data:
                adjustment_message_ref = adjustment_payroll_data.get('PayrollMessageRef', 'UNKNOWN')
                try:
                    _logger.info(f"Sending adjustment payroll to bank with MessageRef: {adjustment_message_ref}")
                    adj_api_result = api_service._make_request(
                        'POST', 
                        '/b2b-rest-payroll-service/b2b/payroll/payment', 
                        adjustment_payroll_data
                    )
                    adjustment_payroll.write({
                        'response_data': json.dumps(adj_api_result, indent=2) if adj_api_result else '',
                        'state': 'sent',
                        'api_reference': adjustment_message_ref,
                        'wps_reference': adjustment_message_ref,
                        'wps_status': 'Sent',
                    })
                    overall_success = overall_success and True
                    responses.append({
                        'type': 'Adjustment Payroll',
                        'status': 'Success',
                        'message': f'Reference: {adjustment_message_ref}'
                    })
                except Exception as e:
                    error_message = str(e)
                    tb = traceback.format_exc()
                    _logger.error(f"Error sending adjustment payroll to bank: {error_message}\n{tb}")
                    adjustment_payroll.write({
                        'response_data': error_message,
                        'state': 'failed'
                    })
                    responses.append({
                        'type': 'Adjustment Payroll',
                        'status': 'Failed',
                        'message': error_message
                    })
            
            # Update original payroll state based on overall success
            if overall_success:
                self.write({
                    'state': 'sent',
                    'wps_status': 'Sent'
                })
                self.payslip_run_id.write({
                    'state': 'sent_to_bank'
                })
            else:
                self.write({
                    'state': 'failed',
                    'wps_status': 'Error: See split payrolls for details'
                })
            
            # Create a detailed message
            message = ""
            for resp in responses:
                message += f"{resp['type']}: {resp['status']} - {resp['message']}\n"
                
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Payroll Processing Complete',
                    'message': message,
                    'sticky': False,
                    'type': 'success' if overall_success else 'warning',
                }
            }
                
        except UserError:
            # Re-raise UserError exceptions without modification
            raise
            
        except Exception as e:
            # Get exception details
            exc_type = type(e).__name__
            exc_tb = traceback.format_exc()
            
            # Log detailed error information
            _logger.error(f"Payroll processing error: {exc_type}: {str(e)}\n{exc_tb}")
            
            # Update record state
            self.write({
                'state': 'failed',
                'wps_status': f'Error: {exc_type}'
            })
            
            # Construct a more informative error message
            error_message = f"Failed to process payroll: {exc_type}: {str(e)}\n\n"
            
            # Add context-specific troubleshooting guidance based on exception type
            if 'connection' in str(e).lower() or 'timeout' in str(e).lower():
                # Update the message to be more helpful
                error_message += "This appears to be a network connectivity issue.\n"
                error_message += "Possible solutions:\n"
                error_message += "1. Check your internet connection\n"
                error_message += "2. Verify the SAIB API endpoint is correct in settings\n"
                error_message += "3. Ensure firewall is not blocking outgoing connections\n"
            elif 'certificate' in str(e).lower() or 'ssl' in str(e).lower():
                error_message += "This appears to be an SSL/TLS certificate issue.\n"
                error_message += "Possible solutions:\n"
                error_message += "1. Verify your client certificates are valid and not expired\n"
                error_message += "2. Check that the certificate paths are correctly configured\n"
                error_message += "3. Ensure the certificate format is correct\n"
            elif 'json' in str(e).lower() or 'parse' in str(e).lower():
                error_message += "This appears to be a data formatting issue.\n"
                error_message += "Possible solutions:\n"
                error_message += "1. Check that all payroll data is correctly formatted\n"
                error_message += "2. Verify that special characters in names or addresses are properly encoded\n"
            else:
                error_message += "Possible solutions:\n"
                error_message += "1. Check the server logs for more detailed error information\n"
                error_message += "2. Verify all required fields are correctly filled\n"
                error_message += "3. Contact support with the error details from the logs\n"
            
            raise UserError(error_message)
    
    # [sanjay-techvoot] Query SAIB to retrieve status for a sent payroll reference.
    # Posts a notification or returns detailed decompressed errors.
    def action_check_status(self):
        """Check the status of a sent payroll"""
        self.ensure_one()
        
        if self.state not in ['sent', 'failed']:
            raise UserError("You can only check status of payrolls that have been sent to the bank")
            
        try:
            # Get API service
            api_service = self.env['saib.api']
            
            # Prepare request data
            config = self.env['ir.config_parameter'].sudo()
            sender = config.get_param('saib_bank_integration.company_code')
            
            payload = {
                "Sender": sender,
                "PayrollMessageRef": self.wps_reference,
                "Receiver": "SIBC",
                "RequestDate": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            # Send request to check status
            response = api_service._make_request(
                'POST', 
                '/b2b-rest-payroll-service/b2b/payroll/inquiry', 
                payload
            )
            
            # Process response
            if response and isinstance(response, dict):
                status_code = response.get('StatusCode')
                status_desc = response.get('StatusDesc', 'No description provided')
                
                if status_code == '000':
                    # Success - get the payroll status
                    payroll_status = response.get('Data', {}).get('Status')
                    self.inquiry_response = json.dumps(response.get('StatusDesc', 'No status description provided'))
                    if payroll_status:
                        status_message = f"Payroll status: {payroll_status}"
                        self.message_post(body=status_message)
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'message': status_message,
                                'sticky': False,
                                'type': 'success',
                            }
                        }
                    else:
                        status_desc = response.get('Data', {}).get('StatusDesc', status_desc)
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Warning'),
                                'message': f"Payroll status: {status_desc}",
                                'sticky': False,
                                'type': 'warning',
                            }
                        }
                else:
                    # Error - try to decompress PayrollDetails if available
                    payroll_details = response.get('PayrollDetails')
                    detailed_error = ""
                    
                    if payroll_details:
                        try:
                            decompressed_data = self._decompress_payroll_data(payroll_details)
                            self.inquiry_response = json.dumps(decompressed_data, indent=2)
                            
                            # Log the decompressed data for debugging
                            _logger.info(f"Decompressed PayrollDetails: {json.dumps(decompressed_data, indent=2)}")
                            
                            # Extract detailed error information if available
                            if isinstance(decompressed_data, dict) and decompressed_data.get('ErrorDetails'):
                                detailed_error = f"\n\nError Details: {decompressed_data.get('ErrorDetails')}"
                            elif isinstance(decompressed_data, list) and decompressed_data:
                                # Sometimes error details are in a list of records with error messages
                                error_records = [rec for rec in decompressed_data if isinstance(rec, dict) and rec.get('ErrorMessage')]
                                if error_records:
                                    detailed_error = "\n\nError Details:\n" + "\n".join([f"• {rec.get('ErrorMessage')}" for rec in error_records])
                            
                            self.message_post(body=f"Decompressed PayrollDetails: {json.dumps(decompressed_data, indent=2)}")
                        except Exception as e:
                            _logger.error(f"Failed to decompress PayrollDetails: {str(e)}")
                            self.inquiry_response = f"Failed to decompress PayrollDetails: {str(e)}\nRaw response: {json.dumps(response)}"
                    else:
                        self.inquiry_response = json.dumps(response)
                    
                    # For "Error in File" specifically, provide more helpful guidance
                    error_message = f"Failed to check status: {status_desc}{detailed_error}"
                    if status_desc == "Error in File. Please see the log for details":
                        error_message += "\n\nThis error typically occurs when there are issues with the data format. Please check:"
                        error_message += "\n1. Employee names - ensure they contain only valid characters"
                        error_message += "\n2. IBAN numbers - ensure they contain no spaces or special characters"
                        error_message += "\n3. Use the 'Test Names' button to validate employee names before submission"
                        error_message += "\n4. Verify that all required fields are properly filled"
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Error'),
                            'message': error_message,
                            'sticky': True,
                            'type': 'danger',
                        }
                    }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _("Invalid response from bank"),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
                
        except Exception as e:
            raise UserError(f"Failed to check payroll status: {str(e)}")
    
    # [sanjay-techvoot] Validate payroll lines and company settings before submission.
    # Returns notification action for warnings or raises UserError on validation errors.
    def action_verify_data(self):
        """Verify payroll data before sending to bank"""
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError('No payroll lines to verify. Please add payroll lines first.')
            
        errors = []
        warnings = []
        
        # Verify employees have bank accounts
        for line in self.line_ids:
            employee = line.employee_id
            
            # Check bank account
            if not employee.bank_account_id:
                errors.append(f'Employee {employee.name} does not have a bank account configured.')
            elif not employee.bank_account_id.acc_number:
                errors.append(f'Employee {employee.name} has an invalid bank account number.')
            else:
                # Validate IBAN format
                clean_iban = self._clean_iban(employee.bank_account_id.acc_number)
                if not clean_iban:
                    errors.append(f'Employee {employee.name} has an empty or whitespace-only IBAN.')
                elif clean_iban != employee.bank_account_id.acc_number:
                    warnings.append(f'Employee {employee.name} IBAN contains whitespace that will be removed.')
            
            # Check national ID
            if not employee.identification_id:
                warnings.append(f'Employee {employee.name} does not have a national ID configured.')
                
            # Validate employee name format
            name_validation = self._preview_clean_customer_name(employee.name)
            if name_validation['status'] == 'invalid':
                errors.append(f'Employee {employee.name} has an invalid name format: {name_validation["message"]}')
            elif name_validation['status'] == 'truncated':
                warnings.append(f'Employee {employee.name} name will be truncated to: {name_validation["cleaned_name"]}')
            
            # Check amount
            if not line.amount or line.amount <= 0:
                errors.append(f'Invalid amount for employee {employee.name}. Amount must be greater than zero.')
            
            # Check name format
            clean_name = self._clean_customer_name(employee.name)
            if clean_name != employee.name:
                if clean_name == "Employee":
                    errors.append(f'Employee {employee.name} has an invalid name format for SAIB bank.')
                elif len(clean_name) < len(employee.name):
                    warnings.append(f'Employee {employee.name} name will be truncated to "{clean_name}".')
        
        # Verify company bank account
        if not self.bank_account_id:
            errors.append('Please configure a bank account for the payroll.')
        elif not self.bank_account_id.acc_number:
            errors.append('The selected bank account is invalid (missing account number).')
        else:
            # Validate company IBAN format
            clean_iban = self._clean_iban(self.bank_account_id.acc_number)
            if not clean_iban:
                errors.append('Company bank account has an empty or whitespace-only IBAN.')
            elif clean_iban != self.bank_account_id.acc_number:
                warnings.append('Company bank account IBAN contains whitespace that will be removed.')
            
        # Verify MOL establishment ID
        if not self.mol_establishment_id:
            errors.append('MOL Establishment ID is required.')
            
        # If errors, show them
        if errors:
            error_message = '\n'.join(errors)
            raise UserError(f"Validation failed:\n{error_message}")
        
        # If only warnings, show them but allow to continue
        if warnings:
            warning_message = '\n'.join(warnings)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Verification Completed with Warnings',
                    'message': f'Payroll data verified with warnings:\n{warning_message}',
                    'sticky': True,
                    'type': 'warning',
                }
            }
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Verification Successful',
                'message': 'All payroll data has been verified successfully.',
                'sticky': False,
                'type': 'success',
            }
        }
    
    # [sanjay-techvoot] Strip whitespace from IBAN/account number and return cleaned string.
    # Returns empty string for invalid/empty inputs.
    def _clean_iban(self, account_number):
        """
        Clean IBAN number by removing all whitespace characters.
        
        Args:
            account_number: The account number to clean
            
        Returns:
            str: Cleaned account number with no whitespace
        """
        # Handle None, False, or empty values
        if account_number is None or account_number is False or account_number == "":
            return ""
            
        # Convert to string if not already
        if not isinstance(account_number, str):
            account_number = str(account_number)
            
        # Remove all whitespace characters (spaces, tabs, newlines)
        cleaned = ''.join(account_number.split())
        
        # Check if the result is empty (was only whitespace)
        if not cleaned:
            return ""
            
        return cleaned
    # [sanjay-techvoot] Clean and validate customer/employee name per SAIB rules.
    # Preserves Arabic names and smart-truncates long non-Arabic names.
    def _clean_customer_name(self, name):
        """
        Clean customer name according to SAIB requirements:
        - Maximum 35 characters
        - Letters, spaces, and diacritical marks only
        - No leading/trailing spaces
        - Must contain at least one letter
        - Preserves Arabic names exactly as they are
        
        Args:
            name: The customer name to clean
        
        Returns:
            str: Cleaned customer name
        """
        if not name:
            return "Employee"
        
        # Ensure name is a string
        if not isinstance(name, str):
            name = str(name) if name is not None else ""
            
        # Check if name contains Arabic characters
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', name))
        
        # For Arabic names, preserve exactly as they are
        if has_arabic:
            # Only check if name is empty
            if not name.strip():
                return "Employee"
                
            # For Arabic names, return as is (no cleaning, no truncation, no trimming)
            return name
        
        # For non-Arabic names, continue with the original cleaning logic
        # Remove hyphens and replace with empty string (e.g., "AL-NASSAR" → "ALNASSAR")
        name = name.replace('-', '')
        
        # Remove special characters (except letters, spaces, and diacritical marks)
        name = re.sub(r'[^\w\s\u00C0-\u017F]', '', name)
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Check if name is empty after cleaning
        if not name:
            return "Employee"
        
        # Check if name contains at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return "Employee"
        
        # Truncate non-Arabic names if longer than 35 characters
        if len(name) > 35:
            # Smart truncation at word boundary
            words = name.split()
            truncated_name = ""
            for word in words:
                if len(truncated_name + " " + word if truncated_name else word) <= 35:
                    truncated_name += " " + word if truncated_name else word
                else:
                    break
                    
            return truncated_name
        else:
            return name

    # [sanjay-techvoot] Preview how a name will be cleaned/truncated and return status/message.
    # Useful for showing warnings before submission.
    def _preview_clean_customer_name(self, name):
        """
        Preview how a customer name will be cleaned according to SAIB requirements:
        - Maximum 35 characters
        - Letters, spaces, and diacritical marks only
        - No leading/trailing spaces
        - Must contain at least one letter
        - Supports Arabic names
        
        Args:
            name: The customer name to preview
            
        Returns:
            dict:
            - original_name: The original name
            - cleaned_name: The cleaned name
            - status: 'valid', 'truncated', or 'invalid'
            - message: A message explaining any issues
        """
        if not name:
            return {
                'original_name': '',
                'cleaned_name': '',
                'status': 'invalid',
                'message': _('Name is empty')
            }
            
        # Ensure name is a string
        if not isinstance(name, str):
            name = str(name) if name is not None else ""
        
        original_name = name
        
        # Check if name contains Arabic characters
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', name))
        
        # Remove hyphens and replace with empty string (e.g., "AL-NASSAR" → "ALNASSAR")
        name = name.replace('-', '')
        
        # For Arabic names, keep the original characters
        # For non-Arabic names, filter out special characters
        if not has_arabic:
            # Remove special characters (except letters, spaces, and diacritical marks)
            name = re.sub(r'[^\w\s\u00C0-\u017F]', '', name)
        else:
            # For Arabic names, only remove truly problematic characters
            # Keep Arabic letters (\u0600-\u06FF), Latin letters, digits, spaces and diacritics
            name = re.sub(r'[^\w\s\u00C0-\u017F\u0600-\u06FF]', '', name)
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Check if name is empty after cleaning
        if not name:
            return {
                'original_name': original_name,
                'cleaned_name': 'Employee',
                'status': 'invalid',
                'message': _('Name contains only special characters')
            }
            
        # Check if name contains at least one letter (Arabic or Latin)
        if not re.search(r'[a-zA-Z\u0600-\u06FF]', name):
            return {
                'original_name': original_name,
                'cleaned_name': 'Employee',
                'status': 'invalid',
                'message': _('Name must contain at least one letter')
            }
            
        # We don't want to transliterate Arabic names
        # Just use smart truncation for all names that exceed 35 characters
            
        # Truncate name if longer than 35 characters
        if len(name) > 35:
            # Smart truncation at word boundaries
            words = name.split()
            truncated_name = ""
            for word in words:
                if len(truncated_name + " " + word if truncated_name else word) <= 35:
                    truncated_name += " " + word if truncated_name else word
                else:
                    break
                    
            return {
                'original_name': original_name,
                'cleaned_name': truncated_name,
                'status': 'truncated',
                'message': _('Name was truncated to fit 35 character limit')
            }
        else:
            return {
                'original_name': original_name,
                'cleaned_name': name,
                'status': 'valid',
                'message': ''
            }

    # [sanjay-techvoot] Generate an Excel report of how names will be formatted (downloadable).
    # Writes file to /tmp and attaches it for user download.
    def action_test_names(self):
        """Test how employee names will be formatted for SAIB bank transactions"""
        self.ensure_one()
        
        if not self.line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Employees'),
                    'message': _('No employees found in this payroll. Please add employees first.'),
                    'type': 'warning',
                }
            }
        
        # Process all employee names
        valid_names = []
        
        # Process each employee
        for line in self.line_ids:
            employee = line.employee_id
            if not employee:
                continue
                
            name_result = self._preview_clean_customer_name(employee.name)
            
            # Add to the appropriate list
            valid_names.append({
                'employee': employee.name,
                'formatted': name_result['cleaned_name'],
                'original': name_result['original_name']
            })
        
        # Create Excel file
        filename = f'name_changes_report_{self.name}.xlsx'
        file_path = os.path.join('/tmp', filename)
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('Name Changes Report')
        
        # Define formats
        header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD', 'border': 1})
        valid_format = workbook.add_format({'bg_color': '#E6FFEC'})  # Light green
        truncated_format = workbook.add_format({'bg_color': '#FFF9C4'})  # Light yellow
        invalid_format = workbook.add_format({'bg_color': '#FFEBEE'})  # Light red
        
        # Add headers
        headers = ['Employee ID', 'Employee Name', 'Original Name', 'Formatted Name', 'Status', 'Message']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 12)  # Employee ID
        worksheet.set_column(1, 2, 30)  # Employee Name, Original Name
        worksheet.set_column(3, 3, 30)  # Formatted Name
        worksheet.set_column(4, 4, 10)  # Status
        worksheet.set_column(5, 5, 40)  # Message
        
        # Add data
        for row, name_data in enumerate(valid_names, start=1):
            # Choose format based on status
            if name_data['status'] == 'valid':
                row_format = valid_format
            elif name_data['status'] == 'truncated':
                row_format = truncated_format
            else:  # invalid
                row_format = invalid_format
                
            worksheet.write(row, 0, name_data['employee_id'], row_format)
            worksheet.write(row, 1, name_data['employee_name'], row_format)
            worksheet.write(row, 2, name_data['original_name'], row_format)
            worksheet.write(row, 3, name_data['formatted_name'], row_format)
            worksheet.write(row, 4, name_data['status'], row_format)
            worksheet.write(row, 5, name_data['message'], row_format)
        
        # Close the workbook
        workbook.close()
        
        # Read the file content
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read())
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
        })
        
        # Return action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    # [sanjay-techvoot] Reset payroll back to draft if not confirmed.
    # Updates state and returns True.
    def action_reset_to_draft(self):
        """Reset the payroll to draft state"""
        self.ensure_one()
        
        if self.state == 'confirmed':
            raise UserError('Cannot reset a confirmed payroll back to draft.')
            
        self.write({'state': 'draft'})
        return True
    
    # [sanjay-techvoot] Request signed payroll file from SAIB and return download action.
    # Creates attachment with signed content when available.
    def action_get_signed_file(self):
        """Get the signed payroll file from SAIB"""
        self.ensure_one()
        
        if self.state not in ['sent', 'confirmed']:
            raise UserError("You can only get a signed file for payrolls that have been sent to the bank")
            
        try:
            # Get API service
            api_service = self.env['saib.api']
            
            # Prepare request data
            config = self.env['ir.config_parameter'].sudo()
            sender = config.get_param('saib_bank_integration.company_code')
            
            payload = {
                "Sender": sender,
                "MessageType": "PRSIGNED",
                "PayrollMessageRef": self.wps_reference,
                "Receiver": "SIBCSARI",
                "RequestDate": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            # Send request to get signed file
            response = api_service._make_request(
                'POST', 
                '/b2b-rest-payroll-service/b2b/payroll/signed', 
                payload
            )
            
            # Process response
            if response and isinstance(response, dict):
                status_code = response.get('StatusCode')
                status_desc = response.get('StatusDesc', 'No description provided')
                signed_content = response.get('SignedContent')
                
                # Log the full response for debugging
                _logger.info(f"SAIB API signed file response: {response}")
                
                if status_code == 'SUCCESS':
                    if signed_content and signed_content != 'NILL':
                        # Create attachment with the signed content
                        attachment_vals = {
                            'name': f"Signed_Payroll_{self.name}.txt",
                            'type': 'binary',
                            'datas': base64.b64encode(signed_content.encode('utf-8')),
                            'res_model': self._name,
                            'res_id': self.id,
                            'mimetype': 'text/plain',
                        }
                        attachment = self.env['ir.attachment'].create(attachment_vals)
                        
                        # Return action to download the attachment
                        return {
                            'type': 'ir.actions.act_url',
                            'url': f'/web/content/{attachment.id}?download=true',
                            'target': 'self',
                        }
                    else:
                        raise UserError(f"No signed content available: {status_desc}")
                else:
                    # Check for specific error about invalid reference
                    if "reference" in status_desc.lower() and "invalid" in status_desc.lower():
                        # Update the message to be more helpful
                        error_message = f"Invalid payroll reference: {self.api_reference}. Please ensure the payroll has been successfully sent to the bank before requesting the signed file."
                    else:
                        error_message = status_desc
                        
                    raise UserError(f"Could not get signed file: {error_message}")
            else:
                raise UserError("Invalid response received from bank")
                
        except Exception as e:
            raise UserError(f"Failed to get signed payroll file: {str(e)}")
    
    # [sanjay-techvoot] Create a secure filename for exports including company info and date.
    # Returns a safe string like 'PayrollDetails_<ref>_<company>_<YYYYMMDD>.xlsx'
    def _get_export_filename(self):
        """Generate secure filename for export with proper company info."""
        # Clean and format company name for secure filename
        company_name = re.sub(r'[^a-zA-Z0-9_-]', '', self.company_id.name or '').replace(' ', '_')
        date_str = fields.Date.today().strftime('%Y%m%d')
        # Add company info for proper identification in multi-company setups
        return f'PayrollDetails_{self.name}_{company_name}_{date_str}.xlsx'
    
    # [sanjay-techvoot] Export payroll details to Excel with metadata and cleaned rows.
    # Writes binary to excel_file field and returns download action.
    def action_export_to_excel(self):
        """Export payroll data to Excel with data cleaning.
        
        This method exports the current payroll data to an Excel file format
        with proper data cleaning according to SAIB Bank requirements.
        """
        self.ensure_one()
        
        # Verify company access for security
        if not self.env['res.company'].browse(self.company_id.id).exists():
            raise AccessError(_("You don't have access to the company of this payroll."))
        
        try:
            # Check if we have inquiry_response data
            inquiry_data = None
            if self.inquiry_response:
                try:
                    inquiry_data = json.loads(self.inquiry_response)
                except (json.JSONDecodeError, ValueError) as e:
                    _logger.warning(f"Could not parse inquiry_response as JSON: {str(e)}")
            
            # If we have valid inquiry data, use it instead of preparing new data
            if inquiry_data and isinstance(inquiry_data, list):
                payroll_details = inquiry_data
            else:
                # Fallback to preparing payroll data with company context
                payroll_data = self.with_context(company_id=self.company_id.id)._prepare_payroll_data()
                
                # Extract PayrollDetails before compression
                if 'PayrollDetails' in payroll_data:
                    payroll_details = payroll_data['PayrollDetails']
                else:
                    raise UserError(_("No payroll details found."))
            
            # Generate secure filename with company info
            filename = self._get_export_filename()
            
            # Create Excel workbook
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            
            # Add metadata worksheet for multi-company environments
            metadata = workbook.add_worksheet('Metadata')
            metadata_header = workbook.add_format({
                'bold': True,
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
            })
            
            metadata_title = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1
            })
            
            # Merge cells for title
            metadata.merge_range(0, 0, 0, 1, 'Payroll Metadata', metadata_title)
            
            # Write metadata with proper company context
            metadata_rows = [
                ('Company', self.company_id.name),
                ('Company ID', self.company_id.id),
                ('Bank Account', self.bank_account_id.acc_number),
                ('Export Date', fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                ('Generated By', self.env.user.name),
                ('Payroll Reference', self.name),
                ('Payroll Date', self.payroll_date),
                ('Status', self.state),
                ('Record Count', len(payroll_details)),
                ('Total Amount', sum(float(record.get('ValueAmount', 0)) for record in payroll_details if isinstance(record, dict))),
            ]
            
            metadata.set_column(0, 0, 20)
            metadata.set_column(1, 1, 40)
            
            row = 1
            for label, value in metadata_rows:
                metadata.write(row, 0, label, metadata_header)
                metadata.write(row, 1, value)
                row += 1
            
            # Add PayrollDetails worksheet
            details = workbook.add_worksheet('PayrollDetails')
            
            # Define professional formats according to standards
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#366092',
                'font_color': 'white',
                'border': 1
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#E6E6E6',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
            })
            
            text_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
            })
            
            number_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
            })
            
            amount_format = workbook.add_format({
                'border': 1,
                'num_format': '#,##0.00',
                'align': 'right',
                'valign': 'vcenter',
            })
            
            deduction_format = workbook.add_format({
                'border': 1,
                'num_format': '#,##0.00',
                'align': 'right',
                'valign': 'vcenter',
                'font_color': 'red',
            })
            
            # Title row with merge
            details.merge_range(0, 0, 0, 13, 'PayrollDetails Report', title_format)
            
            # Define headers following established standards
            headers = [
                'Sequence Number',
                'Transaction Reference',
                'Bank Reference',
                'Value Date',
                'Currency',
                'Amount',
                'Account Number',
                'Customer Name',
                'National ID',
                'Basic Salary',
                'Housing Allowance',
                'Other Earning',
                'Deduction',
                'Status Detail',
            ]
            
            # Write headers
            for col, header in enumerate(headers):
                details.write(1, col, header, header_format)
            
            # Set column widths according to established standards
            column_widths = {
                0: 20,  # Sequence Number
                1: 20,  # Transaction Reference
                2: 15,  # Bank Reference
                3: 12,  # Value Date
                4: 10,  # Currency
                5: 15,  # Amount
                6: 30,  # Account Number
                7: 30,  # Customer Name
                8: 15,  # National ID
                9: 15,  # Basic Salary
                10: 15,  # Housing Allowance
                11: 15,  # Other Earning
                12: 15,  # Deduction
                13: 40,  # Status Detail
            }
            
            for col, width in column_widths.items():
                details.set_column(col, col, width)
            
            # Write data rows with cleaned data
            for row, record in enumerate(payroll_details, start=2):
                # Skip if record is not a dictionary
                if not isinstance(record, dict):
                    continue
                    
                # Clean data according to SAIB requirements
                clean_record = {
                    'SequenceNum': record.get('SequenceNum', ''),
                    'TransactionReference': record.get('TransactionReference', ''),
                    'BankReference': record.get('BenBank', ''),
                    'ValueDate': record.get('ValueDate', ''),
                    'ValueCurrencyCode': record.get('ValueCurrencyCode', ''),
                    'ValueAmount': float(record.get('ValueAmount', 0)),
                    'BenAccountNumber': ''.join(str(record.get('BenAccountNumber', '')).strip().split()),
                    'BenCustomerName': self._clean_customer_name(record.get('BenCustomerName', '')),
                    'NationalId': record.get('NationalId', ''),
                    'BasicSalary': float(record.get('BasicSalary', 0)),
                    'HousingAllowance': float(record.get('HousingAllowance', 0)),
                    'OtherEarning': float(record.get('OtherEarning', 0)),
                    'Deduction': float(record.get('Deduction', 0)),
                    'StatusDetail': record.get('StatusDetail', ''),
                }
                
                details.write(row, 0, clean_record['SequenceNum'], text_format)
                details.write(row, 1, clean_record['TransactionReference'], text_format)
                details.write(row, 2, clean_record['BankReference'], text_format)
                details.write(row, 3, clean_record['ValueDate'], text_format)
                details.write(row, 4, clean_record['ValueCurrencyCode'], text_format)
                details.write(row, 5, clean_record['ValueAmount'], amount_format)
                details.write(row, 6, clean_record['BenAccountNumber'], text_format)
                details.write(row, 7, clean_record['BenCustomerName'], text_format)
                details.write(row, 8, clean_record['NationalId'], text_format)
                details.write(row, 9, clean_record['BasicSalary'], amount_format)
                details.write(row, 10, clean_record['HousingAllowance'], amount_format)
                details.write(row, 11, clean_record['OtherEarning'], amount_format)
                details.write(row, 12, clean_record['Deduction'], deduction_format)
                details.write(row, 13, clean_record['StatusDetail'], text_format)
            
            # Add summary row with proper formatting
            summary_row = len(payroll_details) + 2
            total_amount = sum(float(record.get('ValueAmount', 0)) for record in payroll_details if isinstance(record, dict))
            
            summary_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'right',
                'bg_color': '#E6E6E6',
            })
            
            details.write(summary_row, 0, 'Total Records:', summary_format)
            details.write(summary_row, 1, len(payroll_details), number_format)
            details.write(summary_row, 4, 'Total Amount:', summary_format)
            details.write(summary_row, 5, total_amount, amount_format)
            
            # Close workbook to write to BytesIO
            workbook.close()
            
            # Save the Excel file with company context preserved
            excel_data = base64.b64encode(output.getvalue())
            self.with_context(company_id=self.company_id.id).write({
                'excel_file': excel_data,
                'excel_filename': filename,
            })
            
            # Return action to download file in current company context
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content?model=%s&id=%s&field=excel_file&download=true&filename=%s' % (
                    self._name,
                    self.id,
                    filename,
                ),
                'target': 'self',
            }
            
        except AccessError as e:
            _logger.error(f"Access Error exporting payroll to Excel: {str(e)}\n{traceback.format_exc()}")
            raise
        except UserError as e:
            _logger.error(f"User Error exporting payroll to Excel: {str(e)}\n{traceback.format_exc()}")
            raise
        except Exception as e:
            _logger.error(f"Error exporting payroll to Excel: {str(e)}\n{traceback.format_exc()}")
            raise UserError(_("Error exporting payroll to Excel: %s") % str(e))
    
    # [sanjay-techvoot] Remove whitespace from employee IBANs in this payroll and update records.
    # Returns a notification action summarizing fixes.
    def action_fix_ibans(self):
        """Automatically remove whitespace from all employee IBANs in this payroll"""
        self.ensure_one()
        
        if not self.line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Employees'),
                    'message': _('No employees found in this payroll. Please add employees first.'),
                    'type': 'warning',
                }
            }
        
        # Track which employees had their IBANs fixed
        fixed_ibans = []
        
        for line in self.line_ids:
            employee = line.employee_id
            if not employee or not employee.bank_account_id or not employee.bank_account_id.acc_number:
                continue
                
            # Check if IBAN has whitespace
            original_iban = employee.bank_account_id.acc_number
            cleaned_iban = self._clean_iban(original_iban)
            
            if cleaned_iban and cleaned_iban != original_iban:
                # Update the IBAN
                employee.bank_account_id.acc_number = cleaned_iban
                fixed_ibans.append(employee.name)
        
        # Prepare message
        if fixed_ibans:
            message = f"<strong>✅ Fixed {len(fixed_ibans)} IBANs</strong><br/>"
            message += "Removed whitespace from the following employee IBANs:<br/>"
            for name in fixed_ibans:
                message += f"• {name}<br/>"
        else:
            message = "No IBANs needed fixing. All IBANs are already in the correct format."
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('IBAN Whitespace Removal'),
                'message': message,
                'sticky': True,
                'type': 'success',
            }
        }
    
    # [sanjay-techvoot] Generate an Excel report of name formatting results for all payroll employees.
    # Creates attachment and returns download URL.
    def action_generate_name_report(self):
        """Generate a report of all employee name changes for record-keeping"""
        self.ensure_one()
        
        if not self.line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Employees'),
                    'message': _('No employees found in this payroll. Please add employees first.'),
                    'type': 'warning',
                }
            }
        
        # Create lists for different name categories
        all_names = []
        
        # Process each employee
        for line in self.line_ids:
            employee = line.employee_id
            if not employee:
                continue
                
            name_result = self._preview_clean_customer_name(employee.name)
            
            # Add to the appropriate list
            all_names.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'original_name': name_result['original_name'],
                'formatted_name': name_result['cleaned_name'],
                'status': name_result['status'],
                'message': name_result['message']
            })
        
        # Create Excel file
        filename = f'name_changes_report_{self.name}.xlsx'
        file_path = os.path.join('/tmp', filename)
        
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet('Name Changes Report')
        
        # Define formats
        header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD', 'border': 1})
        valid_format = workbook.add_format({'bg_color': '#E6FFEC'})  # Light green
        truncated_format = workbook.add_format({'bg_color': '#FFF9C4'})  # Light yellow
        invalid_format = workbook.add_format({'bg_color': '#FFEBEE'})  # Light red
        
        # Add headers
        headers = ['Employee ID', 'Employee Name', 'Original Name', 'Formatted Name', 'Status', 'Message']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 12)  # Employee ID
        worksheet.set_column(1, 2, 30)  # Employee Name, Original Name
        worksheet.set_column(3, 3, 30)  # Formatted Name
        worksheet.set_column(4, 4, 10)  # Status
        worksheet.set_column(5, 5, 40)  # Message
        
        # Add data
        for row, name_data in enumerate(all_names, start=1):
            # Choose format based on status
            if name_data['status'] == 'valid':
                row_format = valid_format
            elif name_data['status'] == 'truncated':
                row_format = truncated_format
            else:  # invalid
                row_format = invalid_format
                
            worksheet.write(row, 0, name_data['employee_id'], row_format)
            worksheet.write(row, 1, name_data['employee_name'], row_format)
            worksheet.write(row, 2, name_data['original_name'], row_format)
            worksheet.write(row, 3, name_data['formatted_name'], row_format)
            worksheet.write(row, 4, name_data['status'], row_format)
            worksheet.write(row, 5, name_data['message'], row_format)
        
        # Close the workbook
        workbook.close()
        
        # Read the file content
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read())
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
        })
        
        # Return action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
