drop table if exists entries;
create table entries (
	id integer primary key autoincrement,
	title text not null,
	text text not null,
	img_name text,
	date text not null,
	creator text not null
);
create table users (
	id integer primary key autoincrement,
	username text  unique not null,
	password integer not null,
	salt text not null,
	profilepic_name text,
	date text not null,
	last_active text
);