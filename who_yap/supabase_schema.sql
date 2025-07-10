-- Enable pgvector
create extension if not exists vector;

create table users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  created_at timestamp with time zone default now()
);

create table group_chats (
  id uuid primary key default gen_random_uuid(),
  uploaded_by_username text not null,
  chat_name text
);

create table participants (
  id uuid primary key default gen_random_uuid(),
  group_chat_id uuid references group_chats(id),
  name_on_whatsapp text
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  group_chat_id uuid references group_chats(id),
  participant_id uuid references participants(id),
  timestamp timestamp,
  message_text text
);

create table message_embeddings (
  id uuid primary key default gen_random_uuid(),
  message_id uuid references messages(id),
  embedding vector(1024)
);

create table game_sessions (
  id uuid primary key default gen_random_uuid(),
  group_chat_id uuid references group_chats(id),
  created_by_username text,
  created_at timestamp with time zone default now(),
  is_active boolean default true
);

create table session_players (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references game_sessions(id),
  username text,
  participant_id uuid references participants(id)
);

create table join_requests (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references game_sessions(id),
  requested_by_username text,
  status text check (status in ('pending', 'approved', 'declined')) default 'pending'
);

create table session_answers (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references game_sessions(id),
  player_username text,
  message_id uuid references messages(id),
  selected_participant_id uuid references participants(id),
  is_correct boolean
); 