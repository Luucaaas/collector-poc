#!/bin/sh
# Run only once, on the first start of an empty volume (docker-entrypoint-initdb.d).
# One database and one user per component: none is a superuser, each owns
# its database, and access to each database is removed from PUBLIC (as in experiment 2).
set -e
for entry in catalog:catalog_db:CATALOG_DB_PASSWORD \
             notification:notification_db:NOTIFICATION_DB_PASSWORD \
             keycloak:keycloak:KEYCLOAK_DB_PASSWORD; do
  role=${entry%%:*}; rest=${entry#*:}; db=${rest%%:*}; var=${rest#*:}
  password=$(printenv "$var")
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
       -v role="$role" -v db="$db" -v pw="$password" <<'SQL'
CREATE ROLE :"role" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'pw';
CREATE DATABASE :"db" OWNER :"role";
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
SQL
done
