#!/bin/bash

CONFIG_FILE=config.env
CONFIG_FILE=$(cat $CONFIG_FILE  | sed -r '/[^=]+=[^=]+/!d' | sed -r 's/\s+=\s/=/g')
eval "$CONFIG_FILE"


mysql -e "create database if not exists ${DB_DATABASE} character set utf8 collate utf8_unicode_ci;"
mysql -e "create user if not exists ${DB_USERNAME}@${DB_HOST_ALIAS} identified by '${DB_PASSWORD}';"
mysql -e "grant all on ${DB_DATABASE}.* to ${DB_USERNAME}@${DB_HOST_ALIAS};";
mysql -e "flush privileges";
mysql -e "use ${DB_DATABASE}";
mysql -e "SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''))";
echo "database have been created..."
# create tables 

cat ./database/*.sql | mysql ${DB_DATABASE}
