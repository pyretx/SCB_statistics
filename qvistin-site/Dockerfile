# Qvistin homepage container.
# Build context is the REPO ROOT (so it can copy qvistin-site/). Two stages:
#   1) render dist/ from content.toml + templates/ (single source of truth)
#   2) serve the rendered site with nginx
# Build from repo root:  docker build -f qvistin-site/Dockerfile -t qvistin-site .
FROM python:3.12-slim AS build
WORKDIR /site
COPY qvistin-site/ ./
RUN pip install --no-cache-dir jinja2 && python build.py

FROM nginx:alpine
COPY qvistin-site/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site/dist /usr/share/nginx/html
EXPOSE 80
# Use 127.0.0.1 (not localhost): in the container `localhost` resolves to IPv6 ::1
# but nginx listens on IPv4 only, so a localhost check gets "connection refused"
# and the container is wrongly marked unhealthy (Traefik then won't route to it).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
