FROM mysql:8

ENV MYSQL_ROOT_PASSWORD EthernityNodeExplorer
RUN echo "\
create database if not exists ethernity_explorer2 character set utf8 collate utf8_unicode_ci;\
create user if not exists explorer_admin@172.17.0.1 identified by 'EthernityNodeExplorer';\
grant all on ethernity_explorer2.* to explorer_admin@172.17.0.1;flush privileges;" > /docker-entrypoint-initdb.d/create_db.sql

COPY ../database/* /
RUN  sed -i "s/-- for-windows/use ethernity_explorer2;\n/g" /*.sql

RUN cp /*.sql /docker-entrypoint-initdb.d/

# docker build . -t mysql-image -f windows/Dockerfile && docker run -p 3306:3306 mysql-image 