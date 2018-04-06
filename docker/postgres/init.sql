CREATE DATABASE conduster_db;
CREATE USER docker WITH password 'docker';
GRANT ALL ON DATABASE conduster_db TO docker;
ALTER USER docker CREATEDB;