FROM node:20-slim AS development

WORKDIR /app

COPY package.json .
RUN npm install --no-audit --no-fund

EXPOSE 5173

CMD ["node", "node_modules/vite/bin/vite.js", "--host", "0.0.0.0", "--port", "5173"]
