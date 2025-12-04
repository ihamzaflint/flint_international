from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
import logging
import uuid

_logger = logging.getLogger(__name__)

class GovernmentPayment(models.Model):
    _inherit = 'government.payment'

    def action_pay(self):
        # Call super to create the payments first
        res = super().action_pay()
        
        # Only proceed if we have payment lines and it's a bank payment
        if (self.payment_method == 'bank' and 
            self.payment_type == 'individual' and 
            self.payment_line_ids):
            
            try:
                # Get company bank account
                company_account = self.env['ir.config_parameter'].sudo().get_param('saib_bank_integration.account_number')
                if not company_account:
                    raise UserError(_('SAIB bank account not configured in settings'))
                    
                # Ensure account number is properly formatted (should start with SA for IBAN)
                company_account = str(company_account).strip()
                _logger.info(f"Using company account number: {company_account}")
                if not company_account:
                    raise UserError(_('SAIB bank account number is empty after formatting'))
                if not company_account.startswith('SA'):
                    _logger.warning(f"Account number {company_account} does not appear to be a valid IBAN (should start with SA)")
                
                for line in self.payment_line_ids.filtered(lambda l: l.payment_reference):
                    # Determine which payment scenario to use based on service type
                    is_saddad_service = line.service_type_ids and line.service_type_ids[0].is_saddad_required
                    
                    if is_saddad_service:
                        # Scenario 1: Saddad Service - Pay using Saddad number
                        self._process_saddad_payment(line, company_account)
                    else:
                        # Scenario 2: MOI Service - Pay using Iqama number
                        self._process_moi_payment(line, company_account)
                        
            except Exception as e:
                error_msg = str(e)
                _logger.error(f"Failed to create SAIB payment: {error_msg}")
                self.message_post(body=_('Warning: Payment created but SAIB bank transfer failed. Error: %s') % error_msg)
                raise UserError(_('Warning: Payment created but SAIB bank transfer failed. Error: %s') % error_msg)

        return res
        
    def _process_saddad_payment(self, line, company_account):
        """Process payment for Saddad service using Saddad number"""
        if not line.saddad_no:
            raise UserError(_('Please add Saddad Number to payment line for employee %s') % line.employee_id.name)
        
        # Send payment directly to SAIB bank API using Saddad number
        payment_reference, bank_reference = self._send_direct_payment_to_bank(
            line=line,
            company_account=company_account,
            creditor_account=line.saddad_no,
            payment_type='saddad'
        )
        
        # Link payment reference
        self._link_payment_reference(line, payment_reference, bank_reference)
    
    def _process_moi_payment(self, line, company_account):
        """Process payment for MOI service using Iqama number"""
        if not line.employee_id.visa_no:  # Using visa_no as it's the related field for iqama_no
            raise UserError(_('Please add Iqama Number to employee %s') % line.employee_id.name)
        
        # Send payment directly to SAIB bank API using Iqama number
        payment_reference, bank_reference = self._send_direct_payment_to_bank(
            line=line,
            company_account=company_account,
            creditor_account=line.employee_id.visa_no,
            payment_type='moi'
        )
        
        # Link payment reference
        self._link_payment_reference(line, payment_reference, bank_reference)
    
    def _send_direct_payment_to_bank(self, line, company_account, creditor_account, payment_type):
        """Send payment directly to SAIB bank API"""
        # Generate a unique payment reference and request ID
        reference = self.name.split('/')[1]
        payment_reference = f'{reference}'
        file_ref = f'{fields.Date.today().strftime("%Y%m%d")}' + str(line.id).zfill(6)
        
        # Get the current timestamp in the required format without milliseconds
        # The API expects format: 2024-10-28T06:38:50
        current_time = fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        config = self.env['ir.config_parameter'].sudo()
        sender = config.get_param('saib_bank_integration.company_code') or 'FLINTID'
        
        # Get MOI biller number from system parameters
        config_param = self.env['ir.config_parameter'].sudo()
        moi_biller_number = config_param.get_param('saib_bank_integration.moi_biller_number')
        if not moi_biller_number:
            raise UserError(_('MOI biller number is not configured'))
        
        if payment_type == 'saddad':
            # Format for SADAD utility payments according to the API specification
            # Use a fixed Sender value that complies with SAIB API requirements
            # The API requires an alphanumeric value with max 12 characters
            
            payment_data = {
                "Sender": sender,
                "MessageType": "SADADTRN",  # Must be exactly SADADTRN for SADAD utility payments
                "AccountNumber": company_account,  # Already ensured to be a string and trimmed
                "RequestId": line.id,  # Adding RequestId as required by the API
                "MessageDescription": "SADAD Transaction",  # Match exact description from Postman
                "RequestDate": current_time,  # ISO 8601 format without Z suffix
                "Transaction": {
                    "ReferenceNumber": file_ref,
                    "BillerID": line.biller_id or "001",  # Default biller ID if not provided
                    "BillID": line.bill_number or "",  # Bill number (SADAD number)
                    "BillCategory": line.bill_category or "06",  # Default category if not provided
                    "Amount": str(line.amount),  # Amount as string
                    "PayExactDue": "Y"  # Pay exact due amount
                }
            }
            # Use the SADAD utility payment endpoint
            endpoint = '/b2b-rest-sadad-service/b2b/sadad/utility/payment'
            
        elif payment_type == 'moi':
            # Format for MOI payments according to the API specification
            # Get citizen ID (Iqama/ID number) if available
            citizen_id = line.employee_id.identification_id or line.partner_id.vat or ''
            
            # Use a fixed Sender value that complies with SAIB API requirements
            # The API requires an alphanumeric value with max 12 characters
            
            payment_data = {
                "Sender": sender,
                "MessageType": "SADADMOI",  # Must be exactly SADADMOI for MOI payments
                "AccountNumber": company_account,  # Already ensured to be a string and trimmed
                "RequestId": line.id,  # Adding RequestId as required by the API
                "MessageDescription": "SADAD MOI",  # Match exact description from Postman
                "RequestDate": current_time,  # ISO 8601 format without Z suffix
                "Transaction": {
                    "ReferenceNumber": file_ref,
                    "BillerID": moi_biller_number,  # MOI biller ID from configuration
                    "RequestType": "001",  # Default request type
                    "BillID": citizen_id,  # Use citizen ID as bill ID
                    "Duration": "01"  # Default duration
                }
            }
            
            # Add specific fields based on service type
            service_type = line.service_type_ids and line.service_type_ids[0].name or ''
            if 'driv' in service_type.lower() or 'licen' in service_type.lower():
                payment_data['Transaction']['LicenseType'] = "06"  # Default for driving license
            
            # Use the MOI-specific endpoint
            # Make sure we're using the correct path format without duplicating segments
            endpoint = '/b2b-rest-sadad-service/b2b/sadad/moi/payment'
            
            # Log the endpoint for debugging
            _logger.info(f"Using MOI payment endpoint: {endpoint}")
            
        else:
            # Fallback to standard payment format if neither SADAD nor MOI
            # Get company address details
            company = self.env.company
            debtor_address1 = company.street or company.name
            debtor_address2 = company.street2 or company.city or 'Riyadh'
            debtor_address3 = company.country_id.name if company.country_id else 'Saudi Arabia'
            
            # Ensure company name is alphanumeric and within length limits
            company_name = ''.join(char for char in company.name if char.isalnum())[:35]
            
            payment_data = {
                "ConsentId": payment_reference[:35],  # Ensure ConsentId is not longer than 35 chars
                "InstructionID": payment_reference,
                "TransactionRef": payment_reference,
                "PaymentPurpose": "01",  # Standard payment purpose code
                "Amount": str(line.amount),
                "Currency": 'SAR',
                "ExecutionDate": fields.Date.today().isoformat(),
                "DebtorAccount": {
                    "AccountNumber": company_account,
                    "DebtorName": company_name,  # Use the sanitized company name
                    "AddressDetails": [
                        debtor_address1,
                        debtor_address2,
                        debtor_address3
                    ]
                },
                "CreditorAccount": {
                    "AccountNumber": creditor_account,
                    "CreditorName": "Government of Saudi Arabia",
                    "AddressDetails": [
                        "Government Entity",
                        "Riyadh",
                        "Saudi Arabia"
                    ],
                    "AgentID": "SIBCSARI",  # Default SAIB bank code
                    "AgentName": "The Saudi Investment Bank"
                }
            }
            # Use the standard payment endpoint
            endpoint = '/b2b-rest-payment-service/b2b/payment/single'
        
        # Log the request data for debugging with more details
        _logger.info(f"Sending payment request to SAIB API endpoint: {endpoint}")
        _logger.info(f"Payment data: {payment_data}")
        
        # Validate key fields
        _logger.info(f"Sender: {payment_data.get('Sender')}")
        _logger.info(f"MessageType: {payment_data.get('MessageType')}")
        _logger.info(f"AccountNumber: {payment_data.get('AccountNumber')}")
        
        # Verify key fields based on payment type
        if payment_type in ['saddad', 'moi']:
            if not payment_data.get('MessageType'):
                raise UserError(_('MessageType cannot be empty in SAIB API request'))
            if not payment_data.get('Sender'):
                raise UserError(_('Sender cannot be empty in SAIB API request'))
            if not payment_data.get('AccountNumber'):
                raise UserError(_('AccountNumber cannot be empty in SAIB API request'))
        else:
            if not payment_data.get('InstructionID'):
                raise UserError(_('InstructionID cannot be empty in SAIB API request'))
        
        # Call SAIB API directly
        api = self.env['saib.api']
        response = api._make_request('POST', endpoint, payment_data)
        
        # Extract bank reference from response
        bank_reference = None
        if response and isinstance(response, dict):
            # Check if the payment was successful based on different response formats
            payment_status = response.get('PaymentStatus')
            status = response.get('Status')
            
            # Handle standard payment response format
            if payment_status == 'FAILED':
                status_reason = response.get('StatusReason', 'Unknown reason')
                _logger.error(f"Payment failed: {status_reason}")
                raise UserError(_(f"Payment failed: {status_reason}"))
            
            # Handle SAIB API specific response format with Status field
            if status == 'Fail':
                status_code = response.get('StatusCode', 'Unknown code')
                status_desc = response.get('StatusDesc', 'Unknown error')
                error_message = f"Payment failed: {status_desc} (Code: {status_code})"
                _logger.error(error_message)
                raise ValidationError(_(error_message))
                
            # Try to get the bank reference - adjust based on the new format
            if payment_type in ['saddad', 'moi']:
                # For SADADMOI format, use FileRef as bank reference if BankReference not available
                bank_reference = response.get('Data', {}).get('BankReference') or file_ref
            else:
                bank_reference = response.get('Data', {}).get('BankReference')
                
            if not bank_reference:
                _logger.warning(f"No bank reference received in response: {response}")
        
        # For SADADMOI payments, use the FileRef as payment reference
        if payment_type in ['saddad', 'moi']:
            payment_reference = file_ref
            
        return payment_reference, bank_reference
    
    def _link_payment_reference(self, line, payment_reference, bank_reference):
        """Link payment reference to Odoo payment"""
        if line.payment_reference:
            try:
                # Store the payment reference directly without creating a saib.payment record
                # Use ref instead of payment_ref as that's the correct field name in account.payment
                update_vals = {'ref': payment_reference}
                
                # Check if the payment model has the saib_reference field
                if 'saib_reference' in self.env['account.payment']._fields:
                    update_vals['saib_reference'] = bank_reference
                
                line.payment_reference.write(update_vals)
            except Exception as e:
                _logger.error(f"Error updating payment reference: {e}")
                # Continue processing other payments despite this error
                self.message_post(body=_("Warning: Could not update payment reference for line %s. Error: %s") 
                                % (line.employee_id.name, str(e)))
