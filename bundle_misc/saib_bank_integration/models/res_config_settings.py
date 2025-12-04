import os
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    saib_base_url = fields.Char(
        'SAIB API Base URL',
        config_parameter='saib_bank_integration.base_url',
        default='https://api-test.saib.com'
    )
    saib_company_code = fields.Char(
        'SAIB Company Code',
        config_parameter='saib_bank_integration.company_code',
        help='Company code provided by SAIB bank'
    )
    saib_account_number = fields.Char(
        'SAIB Account Number',
        config_parameter='saib_bank_integration.account_number',
        help='Main account number for SAIB bank transactions'
    )
    saib_client_id = fields.Char(
        'Header Client ID',
        config_parameter='saib_bank_integration.client_id',
        default='565267744747626a9866f10cbfbcec89'
    )
    saib_client_secret = fields.Char(
        'Header Client Secret',
        config_parameter='saib_bank_integration.client_secret',
        default='da746e7e184621a7e66b9d298e230a92'
    )
    saib_data_client_id = fields.Char(
        'Data Client ID',
        config_parameter='saib_bank_integration.data_client_id',
        default='565267744747626a9866f10cbfbcec89'
    )
    saib_data_client_secret = fields.Char(
        'Data Client Secret',
        config_parameter='saib_bank_integration.data_client_secret',
        default='da746e7e184621a7e66b9d298e230a92'
    )
    saib_username = fields.Char(
        'Username',
        config_parameter='saib_bank_integration.username',
        default='almawarid'
    )
    saib_password = fields.Char(
        'Password',
        config_parameter='saib_bank_integration.password'
    )
    saib_customer_ip = fields.Char(
        'Customer IP Address',
        config_parameter='saib_bank_integration.customer_ip',
        default='172.16.38.24'
    )

    saib_moi_biller_number = fields.Char(
        'MOI Biller Number',
        config_parameter='saib_bank_integration.moi_biller_number',
        default='090',
        help='Biller number for Ministry of Interior (MOI) payments'
    )

    saib_cert_path = fields.Char(
        'Client Certificate Path',
        config_parameter='saib_bank_integration.cert_path',
        help='Full path to client-cert.pem file'
    )
    saib_key_path = fields.Char(
        'Client Key Path',
        config_parameter='saib_bank_integration.key_path',
        help='Full path to client-key.pem file'
    )
    
    saib_private_key = fields.Char(
        'JWS Signing Private Key',
        config_parameter='saib_bank_integration.private_key',
        help='RSA private key in PEM format for JWS signing'
    )

    # [sanjay-techvoot] Constraint: Validate format of SAIB private key (header/footer structure).
    # Ensures BEGIN/END lines exist and enough content lines are present.
    @api.constrains('saib_private_key')
    def _check_private_key_format(self):
        for record in self:
            if record.saib_private_key:
                # Basic format validation
                if not record.saib_private_key.startswith('-----BEGIN'):
                    raise ValidationError(_('Invalid private key format: Key must start with -----BEGIN'))
                
                if not record.saib_private_key.endswith('-----'):
                    raise ValidationError(_('Invalid private key format: Key must end with -----'))
                
                # Check for proper structure
                lines = record.saib_private_key.strip().splitlines()
                if len(lines) < 3:  # At minimum: header, content, footer
                    raise ValidationError(_('Invalid private key format: Key is too short'))
                
                # Validate header and footer
                if not lines[0].startswith('-----BEGIN'):
                    raise ValidationError(_('Invalid private key format: Missing BEGIN header'))
                
                if not lines[-1].startswith('-----END'):
                    raise ValidationError(_('Invalid private key format: Missing END footer'))

    # [sanjay-techvoot] Action: Diagnose private key and show results as notification.
    # Uses JWSSigner.diagnose_key_issues for detailed report.
    def action_diagnose_private_key(self):
        """
        Diagnose the private key and show a detailed report to the user.
        This is a helper action for troubleshooting key problems.
        """
        self.ensure_one()
        
        if not self.saib_private_key:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Private Key'),
                    'message': _('No private key is configured. Please enter a private key first.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Import here to avoid circular imports
        from odoo.addons.saib_bank_integration.models.jws_signer import JWSSigner
        
        # Use the diagnostic method
        result = JWSSigner.diagnose_key_issues(self.saib_private_key)
        
        # Create a formatted message
        if result['valid']:
            message = _(' Private key is valid!\n\n')
            message += _('Format: %s\n') % result['format']
            message += _('Line count: %s\n') % result['line_count']
            message += _('Content lines: %s\n') % result['content_line_count']
        else:
            message = _(' Private key is invalid!\n\n')
            message += _('Format: %s\n') % (result['format'] or 'Unknown')
            message += _('Line count: %s\n') % result['line_count']
            message += _('Content lines: %s\n\n') % result['content_line_count']
            
            message += _('Issues detected:\n')
            for issue in result['issues']:
                message += _('- %s\n') % issue
                
            message += _('\nRecommendations:\n')
            for rec in result['recommendations']:
                message += _('- %s\n') % rec
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Private Key Diagnostic Results'),
                'message': message,
                'sticky': True,
                'type': 'warning' if not result['valid'] else 'success',
            }
        }
