#!/bin/bash

apt-get update
apt-get -y install docker-compose

docker-compose stop telus_tv_app tv_redis_cache
docker-compose rm -f telus_tv_app tv_redis_cache

docker-compose up -d --build telus_tv_app tv_redis_cache

exit 0