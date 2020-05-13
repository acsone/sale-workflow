import base64
import io

from PIL import Image

from odoo.tools.float_utils import float_round

from .test_actions_data import ActionsDataCaseBase


def fake_colored_image(color="#4169E1", size=(800, 500)):
    with io.BytesIO() as img_file:
        Image.new("RGB", size, color).save(img_file, "JPEG")
        img_file.seek(0)
        return base64.b64encode(img_file.read())


class ActionsDataDetailCaseBase(ActionsDataCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.package = cls.move_a.move_line_ids.package_id
        cls.lot = cls.env["stock.production.lot"].create(
            {"product_id": cls.product_b.id, "company_id": cls.env.company.id}
        )
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )

    def setUp(self):
        super().setUp()
        with self.work_on_actions() as work:
            self.data = work.component(usage="data_detail")
        with self.work_on_services() as work:
            self.schema = work.component(usage="schema_detail")

    def _expected_location_detail(self, record, **kw):
        return dict(
            **self._expected_location(record),
            **{
                "complete_name": record.complete_name,
                "reserved_move_lines": self.data.move_lines(kw.get("move_lines", [])),
            }
        )

    def _expected_product_detail(self, record, **kw):
        qty_available = record.qty_available
        qty_reserved = float_round(
            record.qty_available - record.free_qty,
            precision_rounding=record.uom_id.rounding,
        )
        detail = {
            "qty_available": qty_available,
            "qty_reserved": qty_reserved,
        }
        if kw.get("full"):
            detail.update(
                {
                    "image": "/web/image/product.product/{}/image_128".format(record.id)
                    if record.image_128
                    else None,
                    "manufacturer": {
                        "id": record.manufacturer.id,
                        "name": record.manufacturer.name,
                    }
                    if record.manufacturer
                    else None,
                    "suppliers": [
                        {
                            "id": v.name.id,
                            "name": v.name.name,
                            "product_name": None,
                            "product_code": v.product_code,
                        }
                        for v in record.seller_ids
                    ],
                }
            )
        return dict(**self._expected_product(record), **detail)


class ActionsDataDetailCase(ActionsDataDetailCaseBase):
    def test_data_location(self):
        location = self.stock_location
        data = self.data.location_detail(location)
        self.assert_schema(self.schema.location_detail(), data)
        move_lines = self.env["stock.move.line"].search(
            [
                ("location_id", "=", location.id),
                ("product_qty", ">", 0),
                ("state", "not in", ("done", "cancel")),
            ]
        )
        self.assertDictEqual(
            data, self._expected_location_detail(location, move_lines=move_lines)
        )

    def test_data_packaging(self):
        data = self.data.packaging(self.packaging)
        self.assert_schema(self.schema.packaging(), data)
        expected = {"id": self.packaging.id, "name": self.packaging.name}
        self.assertDictEqual(data, expected)

    def test_data_lot(self):
        lot = self.env["stock.production.lot"].create(
            {
                "product_id": self.product_b.id,
                "company_id": self.env.company.id,
                "ref": "#FOO",
                "removal_date": "2020-05-20",
                "life_date": "2020-05-31",
            }
        )
        data = self.data.lot_detail(lot)
        self.assert_schema(self.schema.lot_detail(), data)

        expected = {
            "id": lot.id,
            "name": lot.name,
            "ref": "#FOO",
            "product": self._expected_product_detail(self.product_b, full=True),
        }
        # ignore time and TZ, we don't care here
        self.assertEqual(data.pop("removal_date").split("T")[0], "2020-05-20")
        self.assertEqual(data.pop("expire_date").split("T")[0], "2020-05-31")
        self.assertDictEqual(data, expected)

    def test_data_package(self):
        package = self.move_a.move_line_ids.package_id
        package.product_packaging_id = self.packaging.id
        package.package_storage_type_id = self.storage_type_pallet
        # package.invalidate_cache()
        data = self.data.package_detail(package, picking=self.picking)
        self.assert_schema(self.schema.package_detail(), data)

        lines = self.env["stock.move.line"].search(
            [("package_id", "=", package.id), ("state", "not in", ("done", "cancel"))]
        )
        pickings = lines.mapped("picking_id")
        expected = {
            "id": package.id,
            "name": package.name,
            "move_line_count": 1,
            "packaging": self.data.packaging(package.product_packaging_id),
            "weight": 0,
            "pickings": self.data.pickings(pickings),
            "move_lines": self.data.move_lines(lines),
            "storage_type": {
                "id": self.storage_type_pallet.id,
                "name": self.storage_type_pallet.name,
            },
        }
        self.assertDictEqual(data, expected)

    def test_data_picking(self):
        picking = self.picking
        carrier = picking.carrier_id.search([])[0]
        picking.write(
            {
                "origin": "created by test",
                "note": "read me",
                "priority": "3",
                "carrier_id": carrier.id,
            }
        )
        picking.move_lines.write({"date_expected": "2020-05-13"})
        data = self.data.picking_detail(picking)
        self.assert_schema(self.schema.picking_detail(), data)
        expected = {
            "id": picking.id,
            "move_line_count": 4,
            "name": picking.name,
            "note": "read me",
            "origin": "created by test",
            "weight": 110.0,
            "partner": {"id": self.customer.id, "name": self.customer.name},
            "priority": "Very Urgent",
            "operation_type": {
                "id": picking.picking_type_id.id,
                "name": picking.picking_type_id.name,
            },
            "carrier": {"id": carrier.id, "name": carrier.name},
            "lines": self.data.move_lines(picking.move_line_ids),
        }
        self.assertEqual(data.pop("scheduled_date").split("T")[0], "2020-05-13")
        self.maxDiff = None
        self.assertDictEqual(data, expected)

    def test_data_move_line_package(self):
        move_line = self.move_a.move_line_ids
        result_package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.packaging.id}
        )
        move_line.write({"qty_done": 3.0, "result_package_id": result_package.id})
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        product = self.product_a.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 3.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                "packaging": None,
                "weight": 0.0,
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "move_line_count": 0,
                "packaging": self.data.packaging(self.packaging),
                "weight": 0.0,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_lot(self):
        move_line = self.move_b.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        product = self.product_b.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
            },
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_package_lot(self):
        self.maxDiff = None
        move_line = self.move_c.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        product = self.product_c.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
            },
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                "packaging": None,
                "weight": 0.0,
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "move_line_count": 1,
                "packaging": None,
                "weight": 0.0,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_raw(self):
        move_line = self.move_d.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        product = self.product_d.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": None,
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
        }
        self.assertDictEqual(data, expected)

    def test_product(self):
        move_line = self.move_b.move_line_ids
        product = move_line.product_id.with_context(location=move_line.location_id.id)
        manuf = self.env["res.partner"].create({"name": "Manuf 1"})
        product.write(
            {
                "image_128": fake_colored_image(size=(128, 128)),
                "manufacturer": manuf.id,
            }
        )
        vendor_a = self.env["res.partner"].create({"name": "Supplier A"})
        vendor_b = self.env["res.partner"].create({"name": "Supplier B"})
        self.env["product.supplierinfo"].create(
            {
                "name": vendor_a.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUPP1",
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "name": vendor_b.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUPP2",
            }
        )
        data = self.data.product_detail(product)
        self.assert_schema(self.schema.product_detail(), data)
        expected = self._expected_product_detail(product, full=True)
        self.assertDictEqual(data, expected)
