# FROM docker.io/nginx:1.17.8-alpine
# COPY ./compose/production/nginx/default.conf /etc/nginx/conf.d/default.conf

# compose/production/nginx/Dockerfile

FROM docker.io/nginx:1.25-alpine

# Optional: Install curl for debugging (e.g., health checks)
# RUN apk --no-cache add curl

# No COPY of config — managed via docker-compose volume mount
# Nginx will use /etc/nginx/conf.d/default.conf from the mounted file

# Expose port 80 (optional, since docker-compose defines it)
# EXPOSE 80

# CMD is not needed — nginx runs by default