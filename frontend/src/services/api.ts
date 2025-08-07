import axios from 'axios';

// Configuração base da API
const API_BASE_URL = 'http://127.0.0.1:8000';

// Instância do axios com configurações padrão
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutos timeout (aumentado de 30s para 120s)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar logs de requisições (desenvolvimento)
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas e erros
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error);
    
    // Tratar diferentes tipos de erro
    if (error.response) {
      // Erro da API (4xx, 5xx)
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Erro de rede
      console.error('Network Error:', error.request);
    } else {
      // Erro na configuração da requisição
      console.error('Request Setup Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Função para verificar saúde da API
export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API não está respondendo');
  }
};

// API com timeout maior para operações pesadas
export const apiLongTimeout = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutos timeout para operações pesadas
  headers: {
    'Content-Type': 'application/json',
  },
});

// Aplicar os mesmos interceptors
apiLongTimeout.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Long Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Long Request Error:', error);
    return Promise.reject(error);
  }
);

apiLongTimeout.interceptors.response.use(
  (response) => {
    console.log(`✅ API Long Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Long Response Error:', error);
    
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Request Setup Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
