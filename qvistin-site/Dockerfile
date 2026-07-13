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
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1
