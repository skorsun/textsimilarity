# build
FROM node:11.12.0-alpine as build-vue
WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY ./client/package*.json ./
RUN npm install
COPY ./client .
RUN npm run build

# production
FROM python:3.6-alpine as production
WORKDIR /app
RUN apk update && apk add nginx
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
COPY --from=build-vue /app/dist /usr/share/nginx/html
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./server/requirements.txt ./
RUN pip install -r requirements.txt
COPY ./server .
WORKDIR ./server/models
RUN wget https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip && unzip wiki-news-300d-1M.vec.zip
WORKDIR /app/server
CMD python apptor.py