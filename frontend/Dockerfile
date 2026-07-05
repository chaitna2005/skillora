# TestMyKnowledge Frontend - Build stage
FROM node:18-alpine AS build

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# Serve with nginx (listen on PORT for Cloud Run)
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template
RUN rm -f /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.sh"]
