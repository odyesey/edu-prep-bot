# Edu Prep Bot
![image](image.webp)
This bot helps you study by providing community study materials (Videos, images, files, and flashcrads). Add your content, so others can use it too

🏆 Participate in rated tests to be in the top of the leaderboard


## Features
- Leaderboard (sorted by rating)
- Rated tests for verified users only
- Available in two languages: Uzbek and English

And many more features awaiting

## Setup
### Step 1
Before launching bot, create `.env` file in root folder of the project and fill details below

```
BOT_TOKEN=
PRIMARY_LANG=uz (or en)

DB_USER=
DB_PASS=
DB_HOST=
DB_NAME=
```
Note: Use PostgreSQL database

### Step 2
Execute commands below one by one

```
CREATE TABLE public.users (
	user_id int8 NOT NULL,
	rating int4 DEFAULT 100 NOT NULL,
	lang varchar NOT NULL,
	"name" varchar NULL,
	verified bool DEFAULT false NOT NULL,
	saved_resources _int8 DEFAULT '{}'::bigint[] NULL,
	current_vocabulary jsonb DEFAULT '{}'::jsonb NULL,
	current_test int4 NULL,
	current_answers _text NULL,
	results _text NULL,
	CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE public.tests (
	"name" text NOT NULL,
	file_id varchar NOT NULL,
	content_type varchar NOT NULL,
	description text NULL,
	start_time timestamp NULL,
	answers _text NOT NULL,
	rated bool NOT NULL,
	duration interval NULL,
	code int4 NOT NULL,
	CONSTRAINT tests_pk PRIMARY KEY (code)
);


CREATE TABLE public.resources (
	user_id int8 NOT NULL,
	title text NOT NULL,
	file_id text NOT NULL,
	content_type varchar NOT NULL,
	description text NULL,
	keywords _varchar NULL,
	resource_id bigserial NOT NULL,
	saves int8 DEFAULT 0 NOT NULL,
	CONSTRAINT resources_pkey PRIMARY KEY (resource_id)
);

ALTER TABLE public.resources ADD CONSTRAINT resources_users_fk FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

CREATE TABLE public.vocabulary (
	user_id int8 NOT NULL,
	vocabulary_id int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	title text NOT NULL,
	words jsonb NULL,
	keywords _text NULL,
	saves int8 DEFAULT 0 NULL,
	CONSTRAINT vocabulary_pk PRIMARY KEY (vocabulary_id)
);


ALTER TABLE public.vocabulary ADD CONSTRAINT vocabulary_users_fk FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;
```

### Step 3
Install requirements
```
pip install -r requirements.txt
```

### Final step
Launch bot with `python main.py`
