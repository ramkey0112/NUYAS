-- Endesha kwenye Supabase > SQL Editor
create table users (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique not null,
  password_hash text not null,
  city text default 'Mwanza',
  premium_until timestamptz,
  created_at timestamptz default now()
);
create table adhkar (
  id bigserial primary key,
  type text not null check (type in ('asubuhi','jioni')),
  arabic text not null,
  swahili text not null,
  source text,
  created_at timestamptz default now()
);
create table courses (
  id bigserial primary key,
  title text not null,
  description text,
  created_at timestamptz default now()
);
create table lessons (
  id bigserial primary key,
  course_id bigint references courses(id) on delete cascade,
  title text not null,
  body text,
  audio_url text,
  position int default 1,
  is_free boolean default false
);
create table payments (
  id bigserial primary key,
  user_id uuid references users(id) on delete cascade,
  amount int not null,
  method text,
  reference text not null,
  status text default 'pending' check (status in ('pending','approved','rejected')),
  created_at timestamptz default now()
);
alter table users enable row level security;
alter table adhkar enable row level security;
alter table courses enable row level security;
alter table lessons enable row level security;
alter table payments enable row level security;

-- Maudhui ya mfano: MWALIMU AYAHAKIKI kabla ya kuchapisha
insert into adhkar (type, arabic, swahili, source) values
('asubuhi','سُبْحَانَ اللَّهِ وَبِحَمْدِهِ','Ametakasika Allah na kuhimidiwa Yeye. (mara 100)','Hisnul Muslim'),
('asubuhi','أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ','Tumeamka na ufalme ni wa Allah, na sifa njema zote ni za Allah.','Hisnul Muslim'),
('jioni','أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ','Tumeingia jioni na ufalme ni wa Allah, na sifa njema zote ni za Allah.','Hisnul Muslim'),
('jioni','أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ','Najilinda kwa maneno kamili ya Allah kutokana na shari ya alivyoviumba. (mara 3)','Hisnul Muslim');
with c as (insert into courses (title, description) values ('Misingi ya Twahara na Swala','Kozi fupi kwa wanaoanza.') returning id)
insert into lessons (course_id, title, body, position, is_free)
select id, t, b, p, f from c, (values
 ('Utangulizi',' Karibu kwenye kozi. Somo hili ni bure. (Mwalimu aandike maudhui halisi.)',1,true),
 ('Wudhuu','Maudhui ya somo la wudhuu hapa. (Mwalimu ahakiki.)',2,false),
 ('Nguzo za Swala','Maudhui ya nguzo za swala hapa. (Mwalimu ahakiki.)',3,false)
) as v(t,b,p,f);
