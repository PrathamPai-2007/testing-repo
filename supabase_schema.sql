create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  is_admin boolean not null default false,
  generated_quiz_count integer not null default 0,
  last_online_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.quiz_attempts (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.profiles(id) on delete cascade,
  topic text not null,
  difficulty text not null,
  total_questions integer not null,
  answered_questions integer not null,
  correct_answers integer not null,
  accuracy double precision not null,
  score integer not null,
  created_at timestamptz not null default now()
);

create index if not exists quiz_attempts_user_id_idx
  on public.quiz_attempts(user_id);

create or replace function public.is_admin_user()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1
    from public.profiles
    where id = auth.uid()
      and is_admin = true
  );
$$;

alter table public.profiles enable row level security;
alter table public.quiz_attempts enable row level security;

drop policy if exists "users can view own profile" on public.profiles;
create policy "users can view own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

drop policy if exists "users can update own profile" on public.profiles;
create policy "users can update own profile"
on public.profiles
for update
to authenticated
using (auth.uid() = id);

drop policy if exists "users can insert own profile" on public.profiles;
create policy "users can insert own profile"
on public.profiles
for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists "admins can view all profiles" on public.profiles;
create policy "admins can view all profiles"
on public.profiles
for select
to authenticated
using (public.is_admin_user());

drop policy if exists "users can view own quiz attempts" on public.quiz_attempts;
create policy "users can view own quiz attempts"
on public.quiz_attempts
for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "users can insert own quiz attempts" on public.quiz_attempts;
create policy "users can insert own quiz attempts"
on public.quiz_attempts
for insert
to authenticated
with check (auth.uid() = user_id);
