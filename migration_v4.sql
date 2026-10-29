-- Push subscriptions (Web Push — arifa hata browser ikiwa imefungwa)
create table if not exists push_subscriptions (
  id bigserial primary key,
  user_id uuid references users(id) on delete cascade,
  endpoint text unique not null,
  p256dh text not null,
  auth text not null,
  user_agent text,
  created_at timestamptz default now()
);
alter table push_subscriptions enable row level security;

-- In-app notification log (optional history)
create table if not exists notifications (
  id bigserial primary key,
  title text not null,
  body text not null,
  url text,
  kind text default 'broadcast',
  created_by uuid references users(id) on delete set null,
  created_at timestamptz default now()
);
alter table notifications enable row level security;

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
