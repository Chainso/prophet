from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.cli import build_ir
from prophet_cli.cli import parse_ontology
from prophet_cli.cli import validate_ontology
from prophet_cli.codegen.rendering import render_delta_migration
from prophet_cli.codegen.rendering import render_sql


class SqlDisplayIndexTests(unittest.TestCase):
    def _build_ir(self, ontology_text: str) -> dict:
        ontology = parse_ontology(ontology_text)
        errors = validate_ontology(ontology)
        self.assertEqual(errors, [])
        return build_ir(ontology, {})

    def test_sql_schema_adds_display_index_for_explicit_display_key(self) -> None:
        ir = self._build_ir(
            """
ontology Support {
  id "ont_support"
  version "0.1.0"

  object Ticket {
    id "obj_ticket"
    key primary (ticketId)
    key display (externalCode)

    field ticketId {
      id "fld_ticket_id"
      type string
      required
    }

    field externalCode {
      id "fld_ticket_external_code"
      type string
      optional
    }
  }
}
"""
        )

        sql = render_sql(ir)
        self.assertIn("create index if not exists idx_tickets_display on tickets (external_code);", sql)

    def test_sql_schema_skips_display_index_when_display_matches_primary(self) -> None:
        ir = self._build_ir(
            """
ontology IdentityOnly {
  id "ont_identity_only"
  version "0.1.0"

  object User {
    id "obj_user"
    key primary (userId)
    key display (userId)

    field userId {
      id "fld_user_id"
      type string
      required
    }
  }
}
"""
        )

        sql = render_sql(ir)
        self.assertNotIn("idx_users_display", sql)

    def test_delta_migration_updates_display_index_when_display_key_changes(self) -> None:
        old_ir = self._build_ir(
            """
ontology Commerce {
  id "ont_commerce"
  version "0.1.0"

  object Customer {
    id "obj_customer"
    key primary (customerId)

    field customerId {
      id "fld_customer_id"
      type string
      required
    }
  }

  object Order {
    id "obj_order"
    key primary (orderId)
    key display (customer)

    field orderId {
      id "fld_order_id"
      type string
      required
    }

    field customer {
      id "fld_order_customer"
      type ref(Customer)
      required
    }

    field status {
      id "fld_order_status"
      type string
      required
    }
  }
}
"""
        )
        new_ir = self._build_ir(
            """
ontology Commerce {
  id "ont_commerce"
  version "0.2.0"

  object Customer {
    id "obj_customer"
    key primary (customerId)

    field customerId {
      id "fld_customer_id"
      type string
      required
    }
  }

  object Order {
    id "obj_order"
    key primary (orderId)
    key display (status)

    field orderId {
      id "fld_order_id"
      type string
      required
    }

    field customer {
      id "fld_order_customer"
      type ref(Customer)
      required
    }

    field status {
      id "fld_order_status"
      type string
      required
    }
  }
}
"""
        )

        delta_sql, warnings, has_changes, meta = render_delta_migration(old_ir, new_ir)
        self.assertTrue(has_changes)
        self.assertEqual(warnings, [])
        self.assertIn("drop index if exists idx_orders_display;", delta_sql)
        self.assertIn("create index if not exists idx_orders_display on orders (status);", delta_sql)
        self.assertEqual(meta["safe_auto_apply_count"], 1)
        self.assertEqual(meta["manual_review_count"], 0)
        self.assertEqual(meta["destructive_count"], 0)


if __name__ == "__main__":
    unittest.main()
