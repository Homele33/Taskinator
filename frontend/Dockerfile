# Use a lightweight Node.js image as the base
FROM node:24-alpine3.20 

# Set the working directory inside the container
WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy the rest of the source code
COPY . .

# Disable ESLint during build 
ENV NEXT_DISABLE_ESLINT=1

# Use non-failing build command
RUN npm run build 

# Start the application

CMD [ "npm", "run", "start" ]