# Copyright 2020 Akretion Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestSaleMrpLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = self.warehouse.manufacture_pull_id.route_id.id
        route_mto = self.warehouse.mto_pull_id.route_id.id
        self.product_a = self._create_product(
            'Product A', route_ids=[(6, 0, [route_manufacture, route_mto])])
        self.product_b = self._create_product(
            'Product B', route_ids=[(6, 0, [route_manufacture, route_mto])])
        self.component_a = self._create_product('Component A', route_ids=[])
        self.component_b = self._create_product('Component B', route_ids=[])

    def _create_bom(self, template):
        return self.env['mrp.bom'].create({
            'product_tmpl_id': template.id,
            'type': 'normal'})

    def _create_bom_line(self, bom, product, qty):
        self.env['mrp.bom.line'].create({
            'bom_id': bom.id,
            'product_id': product.id,
            'product_qty': qty})

    def _create_product(self, name, route_ids):
        return self.env['product.product'].create({
            'name': name,
            'type': 'product',
            'route_ids': route_ids})

    def _create_sale_order(self, partner, client_ref):
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': client_ref
        })

    def _create_sale_order_line(self, sale_order, product, qty, price, bom):
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': product.id,
            'price_unit': price,
            'product_uom_qty': qty,
            'bom_id': bom.id,
        })

    def test_define_bom_in_sale_line(self):
        """Check manufactured order is created with BOM definied in Sale."""
        # Create BOMs
        bom_a_v1 = self._create_bom(self.product_a.product_tmpl_id)
        self._create_bom_line(bom_a_v1, self.component_a, 1)
        bom_a_v2 = self._create_bom(self.product_a.product_tmpl_id)
        self._create_bom_line(bom_a_v2, self.component_a, 2)

        bom_b_v1 = self._create_bom(self.product_b.product_tmpl_id)
        self._create_bom_line(bom_b_v1, self.component_b, 1)
        bom_b_v2 = self._create_bom(self.product_b.product_tmpl_id)
        self._create_bom_line(bom_b_v2, self.component_b, 2)

        boms = {
            self.product_a.id: bom_a_v2,
            self.product_b.id: bom_b_v2,
        }

        # Create Sale Order
        so = self._create_sale_order(self.partner, "SO1")
        self._create_sale_order_line(so, self.product_a, 1, 10.0, bom_a_v2)
        self._create_sale_order_line(so, self.product_b, 1, 10.0, bom_b_v2)
        so.action_confirm()

        # Check manufacture order
        mos = self.env['mrp.production'].search([('origin', '=', so.name)])
        for mo in mos:
            self.assertEqual(mo.bom_id, boms.get(mo.product_id.id))
