-- Endesha kwenye Supabase SQL Editor (baada ya schema.sql)
alter table users add column if not exists phone text,
  add column if not exists bio text,
  add column if not exists notify_email boolean default true,
  add column if not exists notify_whatsapp boolean default false;
alter table payments add column if not exists order_reference text unique,
  add column if not exists phone text;
alter table payments alter column reference drop not null;
create table if not exists messages (
  id bigserial primary key,
  user_id uuid references users(id) on delete cascade,
  body text not null,
  reply_to bigint,
  reply_name text,
  reply_body text,
  deleted boolean default false,
  created_at timestamptz default now()
);
alter table messages enable row level security;
