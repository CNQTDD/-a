FROM nginx:latest

COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 4173

CMD ["nginx", "-g", "daemon off;"]
