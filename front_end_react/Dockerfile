FROM node:8.4

WORKDIR /usr/src/app

COPY . .

RUN npm install

RUN npm install yarn

RUN yarn

RUN yarn build

RUN npm install pm2 -g

WORKDIR /usr/src/app/dist

EXPOSE 9090

CMD [ "pm2-docker", "server.js" ]
