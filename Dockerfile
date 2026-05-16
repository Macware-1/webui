FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first (layer cache — only reinstalls when deps change)
COPY package.json ./
# Use npm install, not ci, so missing lockfile isn't fatal
RUN npm install

# Copy source AFTER install so node_modules is intact
COPY index.html ./
COPY vite.config.js ./
COPY src/ ./src/

RUN npm run build

# Final stage — only the built output
FROM alpine:3.19
COPY --from=builder /app/dist /dist