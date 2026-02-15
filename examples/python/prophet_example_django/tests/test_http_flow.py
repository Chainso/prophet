from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
GEN_SRC = ROOT / "gen" / "python" / "src"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prophet_example_django.settings")

import django

django.setup()

from django.test import Client
from prophet_example_django.app import initialize_generated_runtime


class DjangoHttpFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        initialize_generated_runtime()
        cls.client = Client()

    def test_action_and_query_http_flow(self) -> None:
        run_id = str(uuid4())
        customer_id = f"user-{run_id}"

        create = self.client.post(
            "/actions/createOrder",
            data=json.dumps(
                {
                    "customer": {"userId": customer_id},
                    "totalAmount": 100.25,
                    "discountCode": "TEST",
                    "tags": ["integration", "python"],
                    "shippingAddress": {
                        "line1": "1 Test St",
                        "city": "San Francisco",
                        "countryCode": "US",
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 200, create.content.decode())
        created = json.loads(create.content.decode())
        order_id = created["order"]["orderId"]
        self.assertEqual(created["currentState"], "created")

        approve = self.client.post(
            "/actions/approveOrder",
            data=json.dumps(
                {
                    "order": {"orderId": order_id},
                    "notes": ["approved"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(approve.status_code, 200, approve.content.decode())
        approved = json.loads(approve.content.decode())
        self.assertEqual(approved["decision"], "approved")
        self.assertEqual(approved["order"]["orderId"], order_id)

        ship = self.client.post(
            "/actions/shipOrder",
            data=json.dumps(
                {
                    "order": {"orderId": order_id},
                    "carrier": "UPS",
                    "trackingNumber": f"trk-{run_id}",
                    "packageIds": ["pkg-1", "pkg-2"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(ship.status_code, 200, ship.content.decode())
        shipped = json.loads(ship.content.decode())
        self.assertEqual(shipped["shipmentStatus"], "shipped")
        self.assertEqual(shipped["order"]["orderId"], order_id)

        fetched = self.client.get(f"/orders/{order_id}")
        self.assertEqual(fetched.status_code, 200, fetched.content.decode())
        fetched_json = json.loads(fetched.content.decode())
        self.assertEqual(fetched_json["orderId"], order_id)
        self.assertEqual(fetched_json["currentState"], "shipped")

        query = self.client.post(
            "/orders/query?page=0&size=10",
            data=json.dumps({"currentState": {"eq": "shipped"}}),
            content_type="application/json",
        )
        self.assertEqual(query.status_code, 200, query.content.decode())
        queried = json.loads(query.content.decode())
        self.assertTrue(any(item["orderId"] == order_id for item in queried["content"]))


if __name__ == "__main__":
    unittest.main()
