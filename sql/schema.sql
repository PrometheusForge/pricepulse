create table if not exists retailers (
  id serial primary key,
  name text not null unique,
  base_url text,
  adapter_key text not null,
  created_at timestamptz default now()
);

create table if not exists products (
  id serial primary key,
  sku text unique not null,
  ean text,
  display_name text not null,
  category text,
  map_price numeric,
  created_at timestamptz default now()
);

create table if not exists retailer_listings (
  id serial primary key,
  product_id int references products(id),
  retailer_id int references retailers(id),
  listing_url text,
  matched_title text,
  match_confidence numeric,
  match_method text,
  created_at timestamptz default now(),
  unique(product_id, retailer_id)
);

create table if not exists price_observations (
  id bigserial primary key,
  listing_id int references retailer_listings(id) on delete cascade,
  price numeric not null,
  currency text default 'GBP',
  in_stock boolean default true,
  observed_at timestamptz default now()
);

create index if not exists idx_price_obs_listing_time
  on price_observations(listing_id, observed_at desc);

alter table products enable row level security;
alter table retailers enable row level security;
alter table retailer_listings enable row level security;
alter table price_observations enable row level security;

create policy "public read products" on products for select using (true);
create policy "public read retailers" on retailers for select using (true);
create policy "public read listings" on retailer_listings for select using (true);
create policy "public read observations" on price_observations for select using (true);