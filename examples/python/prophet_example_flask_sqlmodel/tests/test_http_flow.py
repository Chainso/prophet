from __future__ import annotations

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

import app as example_app


class FlaskSqlModelHttpFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = example_app.app.test_client()

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
        self.assertEqual(create.status_code, 200, create.get_data(as_text=True))
        created = create.get_json()
        order_id = created["order"]["orderId"]
        self.assertEqual(created["currentState"], "created")

        approve = self.client.post(
            "/actions/approveOrder",
            json={
                "order": {"orderId": order_id},
                "notes": ["approved"],
            },
        )
        self.assertEqual(approve.status_code, 200, approve.get_data(as_text=True))
        approved = approve.get_json()
        self.assertEqual(approved["decision"], "approved")
        self.assertEqual(approved["order"]["orderId"], order_id)

        ship = self.client.post(
            "/actions/shipOrder",
            json={
                "order": {"orderId": order_id},
                "carrier": "UPS",
                "trackingNumber": f"trk-{run_id}",
                "packageIds": ["pkg-1", "pkg-2"],
            },
        )
        self.assertEqual(ship.status_code, 200, ship.get_data(as_text=True))
        shipped = ship.get_json()
        self.assertEqual(shipped["shipmentStatus"], "shipped")
        self.assertEqual(shipped["order"]["orderId"], order_id)

        fetched = self.client.get(f"/orders/{order_id}")
        self.assertEqual(fetched.status_code, 200, fetched.get_data(as_text=True))
        fetched_json = fetched.get_json()
        self.assertEqual(fetched_json["orderId"], order_id)
        self.assertEqual(fetched_json["currentState"], "shipped")

        query = self.client.post(
            "/orders/query?page=0&size=10",
            json={"currentState": {"eq": "shipped"}},
        )
        self.assertEqual(query.status_code, 200, query.get_data(as_text=True))
        queried = query.get_json()
        self.assertTrue(any(item["orderId"] == order_id for item in queried["content"]))


if __name__ == "__main__":
    unittest.main()
