-- GENERATED FILE: do not edit directly.
-- Source: configured ontology file (project.ontology_file)

create table if not exists orders (
  order_id text not null,
  customer_user_id text not null,
  total_amount numeric(18,2) not null check (total_amount >= 0),
  discount_code text,
  tags text,
  shipping_address text,
  approved_by_user_id text,
  approval_notes text,
  approval_reason text,
  shipping_carrier text,
  shipping_tracking_number text,
  shipping_package_ids text,
  status text not null check (status in ('Created', 'Approved', 'Shipped')),
  row_version bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fk_orders_customer_user_id foreign key (customer_user_id) references users(user_id),
  primary key (order_id)
);

create index if not exists idx_orders_customer_user_id on orders (customer_user_id);
create index if not exists idx_orders_status on orders (status);

create table if not exists users (
  user_id text not null,
  email text not null,
  row_version bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id)
);
