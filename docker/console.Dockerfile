FROM node:20

WORKDIR /app

COPY apps/console/package.json apps/console/package-lock.json* ./

RUN npm install

COPY apps/console ./

RUN npm run build

CMD ["npm", "run", "start"]
