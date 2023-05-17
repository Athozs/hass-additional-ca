#!/usr/bin/env bash

set -xe

cd "$(dirname "$0")/.."

docker compose stop
docker compose up
