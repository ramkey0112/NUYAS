-- Duration for synchronized global Tafsiri stream
alter table tafsiri_videos add column if not exists duration_sec int;
-- Optional: default 10 min if unknown until client/admin sets real duration
update tafsiri_videos set duration_sec = 600 where duration_sec is null;
