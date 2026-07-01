# --- Stage 1: Build Assets ---
FROM node:20-alpine AS builder

WORKDIR /frontend

# Copy dependencies manifest
COPY package*.json ./

# Install all dependencies (development + production)
RUN npm ci

# Copy codebase and compile production bundle
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build


# --- Stage 2: Runtime Runner ---
FROM node:20-alpine AS runner

WORKDIR /frontend

ENV NODE_ENV=production \
    PORT=3000

# Copy dependencies manifest
COPY package*.json ./

# Install only production dependencies to keep the image slim
RUN npm ci --only=production --silent

# Copy built application directories from builder stage
COPY --from=builder /frontend/.next ./.next
COPY --from=builder /frontend/public ./public

# Ensure the non-root node user owns all files
RUN chown -R node:node /frontend

# Switch execution context to non-root node user
USER node

# Expose Next.js server port
EXPOSE 3000

# Start production server
CMD ["npm", "run", "start"]
