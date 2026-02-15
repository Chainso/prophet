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


class DSLFeaturesTests(unittest.TestCase):
    def test_descriptions_and_composite_display_keys_roundtrip_into_ir(self) -> None:
        ontology_text = """
ontology CommerceLocal {
  id "ont_commerce_local"
  version "0.1.0"
  description "Commerce ontology for local order processing."

  object TenantOrder {
    id "obj_tenant_order"
    description "Tenant-scoped order aggregate."
    key primary (tenantId, orderId)
    key display (externalCode)

    field tenantId {
      id "fld_tenant_order_tenant_id"
      type string
      required
      description "Tenant identifier."
    }

    field orderId {
      id "fld_tenant_order_order_id"
      type string
      required
      documentation "Order identifier."
    }

    field externalCode {
      id "fld_tenant_order_external_code"
      type string
      optional
      description "Human-friendly lookup code."
    }
  }
}
"""
        ontology = parse_ontology(ontology_text)
        errors = validate_ontology(ontology)
        self.assertEqual(errors, [])

        ir = build_ir(ontology, {})
        self.assertEqual(ir["ontology"]["description"], "Commerce ontology for local order processing.")
        obj = next(item for item in ir["objects"] if item["id"] == "obj_tenant_order")
        self.assertEqual(obj["description"], "Tenant-scoped order aggregate.")
        self.assertEqual(
            obj["keys"]["primary"]["field_ids"],
            ["fld_tenant_order_tenant_id", "fld_tenant_order_order_id"],
        )
        self.assertEqual(
            obj["keys"]["display"]["field_ids"],
            ["fld_tenant_order_external_code"],
        )
        field_by_id = {field["id"]: field for field in obj["fields"]}
        self.assertEqual(field_by_id["fld_tenant_order_tenant_id"]["description"], "Tenant identifier.")
        self.assertEqual(field_by_id["fld_tenant_order_order_id"]["description"], "Order identifier.")
        self.assertEqual(field_by_id["fld_tenant_order_external_code"]["description"], "Human-friendly lookup code.")

        contract = next(item for item in ir["query_contracts"] if item["object_id"] == "obj_tenant_order")
        self.assertEqual(contract["paths"]["get_by_id"], "/tenant_orders/{tenantId}/{orderId}")

    def test_object_refs_require_single_field_primary_key_targets(self) -> None:
        ontology_text = """
ontology RefConstraint {
  id "ont_ref_constraint"
  version "0.1.0"

  object Parent {
    id "obj_parent"
    key primary (tenantId, parentId)

    field tenantId {
      id "fld_parent_tenant_id"
      type string
      required
    }

    field parentId {
      id "fld_parent_parent_id"
      type string
      required
    }
  }

  object Child {
    id "obj_child"
    field childId {
      id "fld_child_child_id"
      type string
      required
      key primary
    }
    field parent {
      id "fld_child_parent"
      type ref(Parent)
      required
    }
  }
}
"""
        ontology = parse_ontology(ontology_text)
        errors = validate_ontology(ontology)
        self.assertTrue(any("single-field primary keys" in item for item in errors))

    def test_fields_default_to_required_when_modifier_is_omitted(self) -> None:
        ontology_text = """
ontology RequiredDefaults {
  version "0.1.0"

  object Customer {
    field customerId {
      type string
      key primary
    }

    field nickname {
      type string
      optional
    }
  }
}
"""
        ontology = parse_ontology(ontology_text)
        errors = validate_ontology(ontology)
        self.assertEqual(errors, [])

        customer = next(item for item in ontology.objects if item.name == "Customer")
        field_required = {field.name: field.required for field in customer.fields}
        self.assertTrue(field_required["customerId"])
        self.assertFalse(field_required["nickname"])

    def test_missing_ids_are_auto_generated_and_unique(self) -> None:
        ontology_text = """
ontology MinimalCommerce {
  version "0.1.0"

  object Order {
    field orderId {
      type string
      key primary
    }

    field notes {
      type string
      optional
    }
  }

  action createOrder {
    kind process

    input {
      field notes {
        type string
        optional
      }
    }

    output {
      field order {
        type ref(Order)
      }
    }
  }
}
"""
        ontology = parse_ontology(ontology_text)
        errors = validate_ontology(ontology)
        self.assertEqual(errors, [])

        ir = build_ir(ontology, {})
        ids = [ir["ontology"]["id"]]
        ids.extend(item["id"] for item in ir.get("objects", []))
        for obj in ir.get("objects", []):
            ids.extend(field["id"] for field in obj.get("fields", []))
            ids.extend(state["id"] for state in obj.get("states", []))
            ids.extend(transition["id"] for transition in obj.get("transitions", []))
        ids.extend(item["id"] for item in ir.get("action_inputs", []))
        for shape in ir.get("action_inputs", []):
            ids.extend(field["id"] for field in shape.get("fields", []))
        ids.extend(item["id"] for item in ir.get("action_outputs", []))
        for shape in ir.get("action_outputs", []):
            ids.extend(field["id"] for field in shape.get("fields", []))
        ids.extend(item["id"] for item in ir.get("actions", []))

        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))

        input_names = {shape["name"] for shape in ir.get("action_inputs", [])}
        output_names = {shape["name"] for shape in ir.get("action_outputs", [])}
        self.assertIn("CreateOrderCommand", input_names)
        self.assertIn("CreateOrderResult", output_names)


if __name__ == "__main__":
    unittest.main()
