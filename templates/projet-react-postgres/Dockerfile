# Build multi-étapes : compile le React puis le sert en statique via nginx.
# Adapte selon ton outil de build (Vite -> dist/, Create React App -> build/).

# --- Étape 1 : build ---
FROM node:22-alpine AS build
WORKDIR /app

# Installe les dépendances (cache optimisé : on copie d'abord les manifestes).
COPY package*.json ./
RUN npm ci

# Copie le reste du code et construit.
COPY . .
RUN npm run build      # produit dist/ (Vite) ou build/ (CRA)

# --- Étape 2 : serveur statique ---
FROM nginx:alpine
# Vite produit "dist", Create React App produit "build" : adapte la ligne ci-dessous.
COPY --from=build /app/dist /usr/share/nginx/html
# COPY --from=build /app/build /usr/share/nginx/html   # <- pour Create React App

# Config nginx adaptée aux Single Page Apps (fallback vers index.html).
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
