{
    'name': 'Flint Sale Management',
    'version': '1.0',
    'summary': 'enhance the sale module to be more integrated with the other modules fitting our business needs',
    'description': """
     "
     Sale Order Line Service Model (sale.order.line.service):
     
     This model will be a one-to-many (O2M) field inside each sale.order.line.
     Attributes:
     job_position_name: Name of the job position.
     customer_id: Reference to the customer for whom the recruitment is done.
     salary_range: A tuple or range field specifying the minimum and maximum salary.
     Product Configuration:
     
     Modify the product.product model to include a boolean field is_recruitment_service.
     This flag determines whether the product is associated with recruitment services.
     Sale Order Line Behavior:
     
     When a product linked to a sale.order.line is identified as a recruitment service (i.e., is_recruitment_service is True), trigger the generation of a job position for each line in sale.order.line.service.
     Each job position creation could be linked to a specific workflow or action, such as notifying HR or posting the job to an internal portal.
     Job Application and Cost Analysis Integration:
     
     Once a job application related to a specific job_position_name is accepted, the corresponding sale.order.line.service can be updated with the agreed salary.
     Implement a mechanism where the acceptance of an application sends a confirmation signal to a cost analysis model, which then updates the financial implications accordingly.
     """,
    'category': 'Sales',
    'author': 'Flint International Tech Team. Omar K. Ali',
    'website': 'https://flint-international.com/',
    'depends': [
        'sale',
        'hr',
        'hr_recruitment','utm'],
    'license': 'AGPL-3',
    'data': [
        'reports/sale_order_service_line_template.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/experience_level_views.xml',
        'views/sale_order_service_line_views.xml',
        'data/data.xml'],
    'installable': True
}