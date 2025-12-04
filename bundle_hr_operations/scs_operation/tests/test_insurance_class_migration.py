from odoo.tests.common import TransactionCase

class TestInsuranceClassMigration(TransactionCase):

    def setUp(self, *args, **kwargs):
        super(TestInsuranceClassMigration, self).setUp(*args, **kwargs)
        self.env.cr.execute("ALTER TABLE employee_insurance_line ADD COLUMN insurance_class_char character varying")
        self.env['ir.model.data'].create({
            'name': 'insurance_class_a_plus',
            'module': 'scs_operation',
            'model': 'insurance.class',
            'res_id': self.env.ref('scs_operation.insurance_class_a_plus').id,
        })
        self.env['employee.insurance.line'].create({
            'name': 'Test Insurance Line',
            'insurance_class_char': 'A+',
        })

    def test_migration(self):
        # Manually trigger the migration
        from odoo.addons.scs_operation.migrations.pre import rename_insurance_class_field
        from odoo.addons.scs_operation.migrations.post import migrate_insurance_policy_to_class

        rename_insurance_class_field.migrate(self.env.cr, None)
        migrate_insurance_policy_to_class.migrate(self.env.cr, None)

        # Check if the data has been migrated correctly
        line = self.env['employee.insurance.line'].search([('name', '=', 'Test Insurance Line')])
        self.assertEqual(line.insurance_class.code, 'A+')

    def tearDown(self, *args, **kwargs):
        self.env.cr.execute("ALTER TABLE employee_insurance_line DROP COLUMN IF EXISTS insurance_class_char")
        super(TestInsuranceClassMigration, self).tearDown(*args, **kwargs)
