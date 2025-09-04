# ⚛️ Frontend Dockerfile - React/Vite
FROM node:20-alpine

# Definir variáveis de ambiente
ENV NODE_ENV=development

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apk add --no-cache curl

# Copiar package files
COPY package*.json ./

# Instalar dependências
RUN npm ci --only=production=false

# Copiar código da aplicação
COPY . .

# Criar usuário não-root para segurança
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Mudar ownership dos arquivos
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expor porta
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5173 || exit 1

# Comando padrão para desenvolvimento
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

