-- Live streams (IPTV links editable by admin) + Tafsiri videos
create table if not exists live_streams (
  key text primary key,
  title text not null,
  subtitle text,
  url text not null,
  kind text not null default 'iptv' check (kind in ('iptv','tafsiri')),
  active boolean default true,
  updated_at timestamptz default now()
);

insert into live_streams (key, title, subtitle, url, kind) values
  ('quran_tv', 'Quran TV Live', 'Al Quran Al Kareem', 'http://m.live.net.sa:1935/live/quran/playlist.m3u8', 'iptv'),
  ('makkah', 'Makkah Live', 'Masjid al-Haram & Nabawi', 'http://m.live.net.sa:1935/live/sunnah/playlist.m3u8', 'iptv'),
  ('quran_live', 'Quran Live', 'Tilawa live', 'https://playlist.fasttvcdn.com/pl/dlkqw1ftuvuuzkcb4pxdcg/Iqraafasttv2/playlist.m3u8', 'iptv')
on conflict (key) do nothing;

create table if not exists tafsiri_videos (
  id bigserial primary key,
  title text not null,
  video_url text not null,
  position int not null default 1 check (position between 1 and 114),
  active boolean default true,
  created_at timestamptz default now()
);

create index if not exists tafsiri_videos_pos on tafsiri_videos (position);

alter table live_streams enable row level security;
alter table tafsiri_videos enable row level security;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
