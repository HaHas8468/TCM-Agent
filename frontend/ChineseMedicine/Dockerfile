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

EXPOSE 8080
