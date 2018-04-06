FROM library/postgres
ADD init.sql /docker-entrypoint-initdb.d/
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/postgresql/postgresql.conf
RUN echo "max_connections = 300" >> /var/lib/postgresql/postgresql.conf
RUN echo "shared_buffers = 80MB" >> /var/lib/postgresql/postgresql.conf