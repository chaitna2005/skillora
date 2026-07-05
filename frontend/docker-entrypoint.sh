#!/bin/sh
# Use PORT from Cloud Run (8080) or default 80 for local
PORT="${PORT:-80}"
sed "s/\${PORT}/$PORT/g" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
