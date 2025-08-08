DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user WHERE usename = 'user'
   ) THEN
      CREATE USER "user" WITH PASSWORD 'password';
   END IF;
END
$$;
