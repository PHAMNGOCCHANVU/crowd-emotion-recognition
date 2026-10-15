# ==============================================================================
# Production Dockerfile for Frontend (Multi-stage Build with Nginx)
# ==============================================================================

# Stage 1: Build React với Node.js
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci || npm install

COPY . .
RUN npm run build

# Stage 2: Serve với Nginx Alpine siêu nhẹ (~25MB)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
