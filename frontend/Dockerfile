FROM node:20-bookworm-slim AS patient-build

WORKDIR /build
COPY frontend/ChineseMedicine/package.json frontend/ChineseMedicine/package-lock.json ./
RUN npm ci
COPY frontend/ChineseMedicine/ ./
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build:h5

FROM node:20-bookworm-slim AS doctor-build

WORKDIR /build
COPY frontend/DoctorBackgroundSystem/package.json frontend/DoctorBackgroundSystem/package-lock.json ./
RUN npm ci
COPY frontend/DoctorBackgroundSystem/ ./
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=patient-build /build/dist/build/h5/ /usr/share/nginx/html/patient/
# uni-app H5 使用绝对路径 /static/... 引用图片与图标；显式复制以规避 NAS 构建环境遗漏静态目录。
COPY frontend/ChineseMedicine/src/static/ /tmp/patient-static/
COPY --from=doctor-build /build/dist/ /usr/share/nginx/html/doctor/
RUN mkdir -p /usr/share/nginx/html/patient/static \
    && cp -a /tmp/patient-static/. /usr/share/nginx/html/patient/static/ \
    && chmod -R a+rX /usr/share/nginx/html/patient/static \
    && test -f /usr/share/nginx/html/patient/static/logo.png \
    && test -f /usr/share/nginx/html/patient/static/img/people.svg \
    && test -f /usr/share/nginx/html/patient/static/design-assets/icons/lucide/stethoscope.svg

EXPOSE 8080 3000
