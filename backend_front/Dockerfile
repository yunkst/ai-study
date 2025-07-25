FROM node:24.3.0

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["yarn", "dev"]