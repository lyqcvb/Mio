FROM node:22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

RUN git clone --depth=1 https://github.com/CareyWang/sub-web.git .

COPY customize-subconverter.js /tmp/customize-subconverter.js
RUN node /tmp/customize-subconverter.js
RUN npm install
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
RUN printf '%s\n' \
  'server {' \
  '    listen 80;' \
  '    listen [::]:80;' \
  '    server_name localhost;' \
  '    root /usr/share/nginx/html;' \
  '    index index.html;' \
  '    location /direct-rules {' \
  '        proxy_pass http://mihomo-converter:25600/direct-rules;' \
  '    }' \
  '    location / {' \
  '        try_files $uri $uri/ /index.html;' \
  '    }' \
  '}' \
  > /etc/nginx/conf.d/default.conf
EXPOSE 80
