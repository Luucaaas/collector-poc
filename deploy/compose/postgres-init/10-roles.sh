#!/bin/sh
# Exécuté une seule fois, au premier démarrage d'un volume vide (docker-entrypoint-initdb.d).
# Une base et un utilisateur par composant : aucun n'est superutilisateur, chacun est propriétaire
# de sa base, et l'accès à chaque base est retiré à PUBLIC (comme dans l'expérimentation 2).
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
