drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	img_name text,
	date text not null
);