-- Banner za admin (picha)
create table if not exists banners (
  id bigserial primary key,
  title text,
  image_url text not null,
  link_url text,
  active boolean default true,
  position int default 1,
  created_at timestamptz default now()
);
alter table banners enable row level security;

-- Maswali (admin anauliza) — kama channel
create table if not exists questions (
  id bigserial primary key,
  user_id uuid references users(id) on delete set null,
  body text not null,
  active boolean default true,
  created_at timestamptz default now()
);
alter table questions enable row level security;

-- Majibu ya watumiaji
create table if not exists answers (
  id bigserial primary key,
  question_id bigint references questions(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  body text not null,
  deleted boolean default false,
  created_at timestamptz default now()
);
alter table answers enable row level security;

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- STORAGE: Unda bucket 'banners' (Public) kwenye Supabase → Storage → New bucket
-- Name: banners | Public: ON
