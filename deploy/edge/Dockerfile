FROM node:20-bookworm-slim AS patient-build
WORKDIR /build
COPY frontend/ChineseMedicine/package.json frontend/ChineseMedicine/package-lock.json ./
RUN npm ci
COPY frontend/ChineseMedicine/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build:h5

FROM node:20-bookworm-slim AS doctor-build
WORKDIR /build
COPY frontend/DoctorBackgroundSystem/package.json frontend/DoctorBackgroundSystem/package-lock.json ./
RUN npm ci
COPY frontend/DoctorBackgroundSystem/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=patient-build /build/dist/build/h5/ /usr/share/nginx/html/patient/
COPY --from=doctor-build /build/dist/ /usr/share/nginx/html/doctor/
COPY deploy/edge/http.conf.template /etc/nginx/templates/default.conf.template
