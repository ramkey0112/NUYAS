-- Soma arifa (unread badge)
create table if not exists notification_reads (
  user_id uuid references users(id) on delete cascade,
  notification_id bigint references notifications(id) on delete cascade,
  read_at timestamptz default now(),
  primary key (user_id, notification_id)
);
alter table notification_reads enable row level security;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
