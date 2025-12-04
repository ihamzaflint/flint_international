from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
import json
import unittest.mock as mock
import requests
import uuid
from datetime import datetime

@tagged('post_install', '-at_install')
class TestSaibIntegration(TransactionCase):

    # [sanjay-techvoot] Prepare test environment: create company, config params, bank, accounts and partner.
    # Sets up reusable records used by all test cases.
    def setUp(self):
        super().setUp()
        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })

        # Create test configuration
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.mol_establishment_id', 'TEST123')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.base_url', 'https://api-test.saib.com')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.client_id', '565267744747626a9866f10cbfbcec89')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.client_secret', 'da746e7e184621a7e66b9d298e230a92')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.username', 'testuser')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.password', 'testpass')
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.company_code', 'TESTCO')

        # Create test bank account
        self.bank = self.env['res.bank'].create({
            'name': 'SAIB Bank',
            'bic': 'SIBCSARI'
        })
        
        self.bank_account = self.env['res.partner.bank'].create({
            'acc_number': 'SA1565000000127491101001',
            'bank_id': self.bank.id,
            'company_id': self.company.id,
            'partner_id': self.env.user.partner_id.id,
        })

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'bank_ids': [(0, 0, {
                'acc_number': 'SA5765000000101182018001',
                'bank_id': self.bank.id,
            })]
        })


    # [sanjay-techvoot] Test successful single payment flow: mocks token + payment API and asserts processed state.
    # Creates a saib.payment record and calls the submit action verifying success.
    def test_01_single_payment_success(self):
        """Test successful single payment creation and submission"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock payment response
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'Data': {
                    'ConsentId': '83469b2029b64974',
                    'Status': 'PROCESSED',
                    'StatusReason': 'Payment processed successfully'
                }
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/001',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            payment.action_submit()
            self.assertEqual(payment.state, 'processed')

    # [sanjay-techvoot] Test single payment error path: API returns failure and action_submit should raise UserError.
    # Verifies error handling and propagation of the bank's StatusReason.
    def test_02_single_payment_error(self):
        """Test single payment with error response"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock payment error response
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'Data': {
                    'Status': 'FAILED',
                    'StatusReason': 'Invalid account number'
                }
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/002',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            with self.assertRaises(UserError):
                payment.action_submit()

    # [sanjay-techvoot] Test bulk payment submission: create multiple payments, send bulk, and assert processed state + bank ref.
    # Mocks token and bulk API response to validate aggregation and result handling.            
    def test_03_bulk_payment_success(self):
        """Test successful bulk payment creation and submission"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock bulk payment response
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'Data': {
                    'Status': 'PROCESSED',
                    'StatusReason': 'Bulk payment processed successfully',
                    'BankReference': '1BB2C11044007918'
                }
            }

            # Create multiple payments
            payments = self.env['saib.payment']
            for i in range(3):
                payment = self.env['saib.payment'].create({
                    'name': f'TEST/BULK/{i+1}',
                    'partner_id': self.partner.id,
                    'amount': 1000.00 + i,
                    'currency_id': self.env.ref('base.SAR').id,
                    'bank_account_id': self.bank_account.id,
                    'partner_bank_id': self.partner.bank_ids[0].id,
                    'payment_type': 'bulk',
                    'execution_date': datetime.now(),
                    'payment_purpose': '01',
                })
                payments |= payment

            # Create bulk payment record
            bulk_payment = self.env['saib.payroll'].create({
                'name': 'TEST/BULK/001',
                'payment_date': datetime.now(),
                'currency_id': self.env.ref('base.SAR').id,
                'payment_ids': [(6, 0, payments.ids)]
            })

            bulk_payment.action_send_to_bank()
            self.assertEqual(bulk_payment.state, 'processed')
            self.assertEqual(bulk_payment.bank_reference, '1BB2C11044007918')

    # [sanjay-techvoot] Test checking payment status: mocks status API and verifies payment state and bank reference are updated.
    # Ensures action_check_status parses response and updates record fields.
    def test_04_payment_status_check(self):
        """Test payment status check functionality"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock status check response
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'Data': {
                    'Status': 'PROCESSED',
                    'StatusReason': 'Payment processed successfully',
                    'BankReference': 'REF123456'
                }
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/003',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            payment.action_check_status()
            self.assertEqual(payment.state, 'processed')
            self.assertEqual(payment.bank_reference, 'REF123456')

    # [sanjay-techvoot] Test handling of invalid auth token: simulate 401 token response and expect UserError.
    # Confirms authentication errors are surfaced with the provider's error message.
    def test_05_invalid_token(self):
        """Test handling of invalid authentication token"""
        with mock.patch('requests.post') as mock_post:
            # Mock token error response
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {
                'error': 'invalid_token',
                'error_description': 'Token is expired or invalid'
            }
            
            payment = self.env['saib.payment'].create({
                'name': 'TEST/004',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })
            
            with self.assertRaises(UserError) as e:
                payment.action_submit()
            self.assertIn('Token is expired or invalid', str(e.exception))

    # [sanjay-techvoot] Test network timeout during token retrieval: simulate requests Timeout and expect UserError.
    # Verifies timeout exceptions are caught and reported by the submit flow.
    def test_06_network_timeout(self):
        """Test handling of network timeout"""
        with mock.patch('requests.post') as mock_post:
            # Mock network timeout
            mock_post.side_effect = requests.exceptions.Timeout()
            
            payment = self.env['saib.payment'].create({
                'name': 'TEST/005',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })
            
            with self.assertRaises(UserError) as e:
                payment.action_submit()
            self.assertIn('timeout', str(e.exception).lower())

    # [sanjay-techvoot] Test unexpected/invalid API response format: ensure submit raises UserError on malformed responses.
    # Mocks token and a non-conforming payment response to validate defensive parsing.
    def test_07_invalid_response_format(self):
        """Test handling of invalid API response format"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock invalid response format
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'InvalidFormat': 'This is not the expected response format'
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/006',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            with self.assertRaises(UserError) as e:
                payment.action_submit()
            self.assertIn('invalid', str(e.exception).lower())

    # [sanjay-techvoot] Test idempotency handling: ensure duplicate requests return proper error and first succeeds.
    # Mocks UUID and request responses to verify idempotency-key behavior and duplicate detection.
    def test_08_idempotency_check(self):
        """Test idempotency key handling for duplicate requests"""
        with mock.patch('requests.post') as mock_post, \
             mock.patch('requests.request') as mock_request, \
             mock.patch('uuid.uuid4') as mock_uuid:
            
            # Mock token response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'access_token': 'test_token'}

            # Mock UUID for consistent idempotency key
            mock_uuid.return_value = 'test-uuid-4321'

            # Mock first request success
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {
                'Data': {
                    'Status': 'PROCESSED',
                    'StatusReason': 'Payment processed successfully',
                    'BankReference': 'REF123456'
                }
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/007',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            # First submission should succeed
            payment.action_submit()
            self.assertEqual(payment.state, 'processed')
            self.assertEqual(payment.bank_reference, 'REF123456')

            # Mock duplicate request response
            mock_request.return_value.status_code = 409
            mock_request.return_value.json.return_value = {
                'error': 'duplicate_request',
                'message': 'Request with this idempotency key already processed'
            }

            # Second submission should raise error
            with self.assertRaises(UserError) as e:
                payment.action_submit()
            self.assertIn('duplicate', str(e.exception).lower())
        with mock.patch('requests.post') as mock_post:
            # Mock token error response
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {
                'error': 'invalid_client',
                'error_description': 'Invalid client credentials'
            }

            payment = self.env['saib.payment'].create({
                'name': 'TEST/004',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            with self.assertRaises(UserError) as context:
                payment.action_submit()
            self.assertIn('Failed to authenticate with SAIB', str(context.exception))

    # [sanjay-techvoot] Test network connection errors during token fetch: simulate ConnectionError and raise UserError.
    # Verifies connection exceptions produce clear failure messages during submission.
    def test_06_network_error(self):
        """Test handling of network errors"""
        with mock.patch('requests.post') as mock_post:
            # Mock network error
            mock_post.side_effect = requests.exceptions.ConnectionError('Failed to connect')

            payment = self.env['saib.payment'].create({
                'name': 'TEST/005',
                'partner_id': self.partner.id,
                'amount': 1000.05,
                'currency_id': self.env.ref('base.SAR').id,
                'bank_account_id': self.bank_account.id,
                'partner_bank_id': self.partner.bank_ids[0].id,
                'payment_type': 'single',
                'execution_date': datetime.now(),
                'payment_purpose': '01',
            })

            with self.assertRaises(UserError) as context:
                payment.action_submit()
            self.assertIn('Failed to connect', str(context.exception))

    
    # [sanjay-techvoot] Test missing configuration handling: clear required param and expect UserError on submit.
    # Ensures validation of required SAIB settings before attempting API calls.
    def test_07_missing_configuration(self):
        """Test handling of missing configuration parameters"""
        # Remove required configuration
        self.env['ir.config_parameter'].sudo().set_param('saib_bank_integration.client_id', '')
        
        payment = self.env['saib.payment'].create({
            'name': 'TEST/006',
            'partner_id': self.partner.id,
            'amount': 1000.05,
            'currency_id': self.env.ref('base.SAR').id,
            'bank_account_id': self.bank_account.id,
            'partner_bank_id': self.partner.bank_ids[0].id,
            'payment_type': 'single',
            'execution_date': datetime.now(),
            'payment_purpose': '01',
        })

        with self.assertRaises(UserError) as context:
            payment.action_submit()
        self.assertIn('Missing configuration', str(context.exception))
