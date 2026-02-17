from __future__ import annotations

import sys
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
GEN_SRC = ROOT / "gen" / "python" / "src"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(GEN_SRC) not in sys.path:
    sys.path.insert(0, str(GEN_SRC))

import app as example_app


class FastApiSqlModelHttpFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.client = TestClient(example_app.app)

    def test_action_and_query_http_flow(self) -> None:
        run_id = str(uuid4())
        customer_id = f"user-{run_id}"

        create = self.client.post(
            "/actions/createOrder",
            json={
                "customer": {"userId": customer_id},
                "totalAmount": 100.25,
                "discountCode": "TEST",
                "tags": ["integration", "python"],
                "shippingAddress": {
                    "line1": "1 Test St",
                    "city": "San Francisco",
                    "countryCode": "US",
                },
            },
        )
        self.assertEqual(create.status_code, 200, create.text)
        created = create.json()
        order_id = created["order"]["orderId"]

        approve = self.client.post(
            "/actions/approveOrder",
            json={
                "order": {"orderId": order_id},
                "notes": ["approved"],
            },
        )
        self.assertEqual(approve.status_code, 200, approve.text)
        approved = approve.json()
        self.assertEqual(approved["orderId"], order_id)
        self.assertEqual(approved["fromState"], "created")
        self.assertEqual(approved["toState"], "approved")

        ship = self.client.post(
            "/actions/shipOrder",
            json={
                "order": {"orderId": order_id},
                "carrier": "UPS",
                "trackingNumber": f"trk-{run_id}",
                "packageIds": ["pkg-1", "pkg-2"],
            },
        )
        self.assertEqual(ship.status_code, 200, ship.text)
        shipped = ship.json()
        self.assertEqual(shipped["orderId"], order_id)
        self.assertEqual(shipped["fromState"], "approved")
        self.assertEqual(shipped["toState"], "shipped")

        fetched = self.client.get(f"/orders/{order_id}")
        self.assertEqual(fetched.status_code, 200, fetched.text)
        fetched_json = fetched.json()
        self.assertEqual(fetched_json["orderId"], order_id)
        self.assertEqual(fetched_json["state"], "shipped")

        query = self.client.post(
            "/orders/query?page=0&size=10",
            json={
                "state": {"eq": "shipped"},
                "orderId": {"eq": order_id},
            },
        )
        self.assertEqual(query.status_code, 200, query.text)
        queried = query.json()
        self.assertTrue(any(item["orderId"] == order_id for item in queried["content"]))


if __name__ == "__main__":
    unittest.main()
