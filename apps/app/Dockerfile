FROM node:22.19.0-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS development
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM dependencies AS build
COPY . .
RUN npm run build

FROM node:22.19.0-alpine AS production
ENV NODE_ENV=production
WORKDIR /app
RUN addgroup -S processos && adduser -S processos -G processos
COPY --from=build --chown=processos:processos /app/.next/standalone ./
COPY --from=build --chown=processos:processos /app/.next/static ./.next/static
COPY --from=build --chown=processos:processos /app/public ./public
USER processos
EXPOSE 3000
CMD ["node", "server.js"]
