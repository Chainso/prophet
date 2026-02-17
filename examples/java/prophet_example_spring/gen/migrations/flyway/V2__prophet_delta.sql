-- GENERATED FILE: do not edit directly.
-- Source: baseline IR -> current IR delta migration
-- SAFETY: destructive_changes=false
-- SAFETY: backfill_required=false
-- SAFETY: manual_review_required=false
-- SAFETY: safe_auto_apply_count=6
-- SAFETY: manual_review_count=0
-- SAFETY: destructive_count=0

alter table orders add column if not exists approval_notes text;
alter table orders add column if not exists approval_reason text;
alter table orders add column if not exists approved_by_user_id text;
alter table orders add column if not exists shipping_carrier text;
alter table orders add column if not exists shipping_package_ids text;
alter table orders add column if not exists shipping_tracking_number text;
