FROM node:24

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Vite는 VITE_* 환경변수를 빌드 타임에 번들에 굽기 때문에 런타임이 아닌 build arg로 받아야 한다.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
