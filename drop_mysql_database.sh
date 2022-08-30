#!/bin/bash

CONFIG_FILE=config.env
CONFIG_FILE=$(cat $CONFIG_FILE  | sed -r '/[^=]+=[^=]+/!d' | sed -r 's/\s+=\s/=/g')
eval "$CONFIG_FILE"


mysql -e "drop database if exists ${DB_DATABASE};"
mysql -e "drop user if exists ${DB_USERNAME}@${DB_HOST_ALIAS}";
mysql -e "flush privileges";

echo "database have been deleted..."