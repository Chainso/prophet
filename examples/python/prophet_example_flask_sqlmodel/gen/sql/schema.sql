-- GENERATED FILE: do not edit directly.
-- Source: configured ontology file (project.ontology_file)

create table if not exists prophet_state_catalog (
  object_model_id text not null,
  state_id text not null,
  state_name text not null,
  is_initial boolean not null,
  primary key (object_model_id, state_id),
  unique (object_model_id, state_name)
);

create table if not exists prophet_transition_catalog (
  object_model_id text not null,
  transition_id text not null,
  from_state_id text not null,
  to_state_id text not null,
  primary key (object_model_id, transition_id)
);

insert into prophet_state_catalog (object_model_id, state_id, state_name, is_initial)
values
  ('obj_order', 'state_order_created', 'created', true),
  ('obj_order', 'state_order_approved', 'approved', false),
  ('obj_order', 'state_order_shipped', 'shipped', false)
on conflict do nothing;

insert into prophet_transition_catalog (object_model_id, transition_id, from_state_id, to_state_id)
values
  ('obj_order', 'trans_order_approve', 'state_order_created', 'state_order_approved'),
  ('obj_order', 'trans_order_ship', 'state_order_approved', 'state_order_shipped')
on conflict do nothing;

create table if not exists orders (
  order_id text not null,
  customer_user_id text not null,
  total_amount numeric(18,2) not null check (total_amount >= 0),
  discount_code text,
  tags text,
  shipping_address text,
  __prophet_state text not null check (__prophet_state in ('CREATED', 'APPROVED', 'SHIPPED')),
  row_version bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint fk_orders_customer_user_id foreign key (customer_user_id) references users(user_id),
  primary key (order_id)
);

create index if not exists idx_orders_customer_user_id on orders (customer_user_id);
create index if not exists idx_orders___prophet_state on orders (__prophet_state);

create table if not exists order_state_history (
  history_id bigserial primary key,
  order_id text not null,
  transition_id text not null,
  from_state text not null,
  to_state text not null,
  changed_at timestamptz not null default now(),
  changed_by text,
  constraint fk_order_state_history_entity foreign key (order_id) references orders(order_id)
);
create index if not exists idx_order_state_history_entity on order_state_history (order_id);
create index if not exists idx_order_state_history_changed_at on order_state_history (changed_at);

create table if not exists users (
  user_id text not null,
  email text not null,
  row_version bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id)
);
