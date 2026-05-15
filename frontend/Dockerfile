# =====================================================
# Stage 1: Build the Application
# =====================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies and install them
COPY package*.json ./
RUN npm install

# Copy all your source code
COPY . .

# Compile the Next.js app into the tiny 'standalone' version
RUN npm run build

# ==========================================================
# Stage 2: Production Server (The Final Image)
# ==========================================================
FROM node:20-alpine AS runner

WORKDIR /app
ENV MODE_ENV=production

# Copy ONLY the essential compiled files from the 'builder' stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# Run the lightweight standalone server (no 'npm run dev' needed!)
CMD ["node", "server.js"]
