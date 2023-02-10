#!/bin/sh
# run in update repository (adjust save_csv if necessary)
git pull
echo '{ "save_csv": true }' > config.json
docker-compose up -d --build