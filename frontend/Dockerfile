FROM node:20-alpine

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Next.js dev server with hot-reload
CMD ["npm", "run", "dev"]
