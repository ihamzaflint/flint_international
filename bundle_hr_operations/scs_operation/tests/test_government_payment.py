from odoo.tests import TransactionCase
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class TestGovernmentPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create test data
        self.company = self.env.company
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'visa_no': '1234567890',
            'visa_expire': datetime.today(),
        })
        self.project = self.env['client.project'].create({
            'name': 'Test Project',
            'partner_id': self.env['res.partner'].create({'name': 'Test Partner'}).id,
        })
        self.service_type = self.env['service.type'].create({
            'name': 'Test Service',
            'service_type': 'individual',
            'is_saddad_required': True,
            'default_credit_account_id': self.env['account.account'].search([('account_type', '=', 'asset_current')], limit=1).id,
            'default_debit_account_id': self.env['account.account'].search([('account_type', '=', 'expense')], limit=1).id,
        })
        # Create a journal for government payments
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TST',
            'type': 'bank',
            'company_id': self.company.id,
        })
        # Set the default journal in settings
        self.env['res.config.settings'].create({
            'gov_pay_default_journal_id': self.journal.id,
        }).execute()

    def test_01_create_individual_payment(self):
        """Test creating an individual government payment"""
        # Create a government payment
        payment = self.env['government.payment'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'service_type_ids': [(4, self.service_type.id)],
            'payment_type': 'individual',
            'operation_type': 'with_payment',
            'effective_date': datetime.today(),
            'payment_method': 'bank',
            'company_id': self.company.id,
        })
        
        # Create a payment line
        payment_line = self.env['government.payment.line'].create({
            'government_payment_id': payment.id,
            'employee_id': self.employee.id,
            'amount': 1000.0,
            'service_type_ids': [(4, self.service_type.id)],
            'saddad_no': '123456789',
            'company_id': self.company.id,
        })

        # Test initial state
        self.assertEqual(payment.state, 'draft', "New payment should be in draft state")
        self.assertEqual(payment_line.payment_state, 'not_paid', "New payment line should be in not_paid state")

        # Submit payment
        payment.action_submit()
        self.assertEqual(payment.state, 'submit', "Payment should be in submit state after submission")

        # Approve payment
        payment.action_approve()
        self.assertEqual(payment.state, 'approve', "Payment should be in approve state after approval")

        # Pay payment
        payment.action_pay()
        self.assertEqual(payment.state, 'paid', "Payment should be in paid state after payment")
        self.assertEqual(payment_line.payment_state, 'paid', "Payment line should be in paid state after payment")

    def test_02_create_enterprise_payment(self):
        """Test creating an enterprise government payment"""
        # Create a government payment
        payment = self.env['government.payment'].create({
            'project_id': self.project.id,
            'service_type_id': self.service_type.id,
            'payment_type': 'enterprise',
            'operation_type': 'with_payment',
            'effective_date': datetime.today(),
            'payment_method': 'bank',
            'company_id': self.company.id,
            'saddad_no': '987654321',
            'total_amount': 2000.0,
        })

        # Test initial state
        self.assertEqual(payment.state, 'draft', "New payment should be in draft state")

        # Submit payment
        payment.action_submit()
        self.assertEqual(payment.state, 'submit', "Payment should be in submit state after submission")

        # Approve payment
        payment.action_approve()
        self.assertEqual(payment.state, 'approve', "Payment should be in approve state after approval")

        # Pay payment
        payment.action_pay()
        self.assertEqual(payment.state, 'paid', "Payment should be in paid state after payment")

    def test_03_payment_validations(self):
        """Test payment validations"""
        # Test creating payment without required Saddad number
        with self.assertRaises(UserError):
            payment = self.env['government.payment'].create({
                'project_id': self.project.id,
                'service_type_id': self.service_type.id,
                'payment_type': 'enterprise',
                'operation_type': 'with_payment',
                'effective_date': datetime.today(),
                'payment_method': 'bank',
                'company_id': self.company.id,
                'total_amount': 2000.0,
            })
            payment.action_submit()

        # Test creating payment line with negative amount
        with self.assertRaises(UserError):
            self.env['government.payment.line'].create({
                'government_payment_id': self.env['government.payment'].create({
                    'employee_id': self.employee.id,
                    'project_id': self.project.id,
                    'service_type_ids': [(4, self.service_type.id)],
                    'payment_type': 'individual',
                    'operation_type': 'with_payment',
                    'effective_date': datetime.today(),
                    'payment_method': 'bank',
                    'company_id': self.company.id,
                }).id,
                'employee_id': self.employee.id,
                'amount': -100.0,
                'service_type_ids': [(4, self.service_type.id)],
                'saddad_no': '123456789',
                'company_id': self.company.id,
            })

    def test_04_payment_computation(self):
        """Test payment computations"""
        # Create a government payment with multiple lines
        payment = self.env['government.payment'].create({
            'employee_id': self.employee.id,
            'project_id': self.project.id,
            'service_type_ids': [(4, self.service_type.id)],
            'payment_type': 'individual',
            'operation_type': 'with_payment',
            'effective_date': datetime.today(),
            'payment_method': 'bank',
            'company_id': self.company.id,
        })
        
        # Create multiple payment lines
        line1 = self.env['government.payment.line'].create({
            'government_payment_id': payment.id,
            'employee_id': self.employee.id,
            'amount': 1000.0,
            'service_type_ids': [(4, self.service_type.id)],
            'saddad_no': '123456789',
            'company_id': self.company.id,
        })
        
        line2 = self.env['government.payment.line'].create({
            'government_payment_id': payment.id,
            'employee_id': self.employee.id,
            'amount': 2000.0,
            'service_type_ids': [(4, self.service_type.id)],
            'saddad_no': '987654321',
            'company_id': self.company.id,
        })

        # Test total amount computation
        self.assertEqual(payment.total_amount, 3000.0, "Total amount should be sum of all payment lines")

        # Test payment count computation
        payment.action_pay()
        self.assertEqual(payment.payment_count, 2, "Payment count should be equal to number of payment lines")
