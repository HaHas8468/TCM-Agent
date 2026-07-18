FROM node:20-bookworm-slim AS build

WORKDIR /build
COPY frontend/ChineseMedicine/package.json frontend/ChineseMedicine/package-lock.json ./
RUN npm ci
COPY frontend/ChineseMedicine/ ./
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build:h5

FROM nginx:1.27-alpine

COPY frontend/ChineseMedicine/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist/build/h5/ /usr/share/nginx/html/
# H5 页面以 /static/... 访问资源，部署镜像中显式保留该目录。
COPY frontend/ChineseMedicine/src/static/ /tmp/patient-static/
RUN mkdir -p /usr/share/nginx/html/static \
    && cp -a /tmp/patient-static/. /usr/share/nginx/html/static/ \
    && chmod -R a+rX /usr/share/nginx/html/static \
    && test -f /usr/share/nginx/html/static/logo.png \
    && test -f /usr/share/nginx/html/static/img/people.svg \
    && test -f /usr/share/nginx/html/static/design-assets/icons/lucide/stethoscope.svg

EXPOSE 8080
