type CacheEntry<T> = {
  data: T;
  timestamp: number;
  expiresIn: number;
};

type CacheStore = {
  [key: string]: CacheEntry<unknown>;
};

class ApiCache {
  private cache: CacheStore = {};
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutos

  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    this.cache[key] = {
      data,
      timestamp: Date.now(),
      expiresIn: ttl,
    };
  }

  get<T>(key: string): T | null {
    const entry = this.cache[key];
    
    if (!entry) {
      return null;
    }

    const isExpired = Date.now() - entry.timestamp > entry.expiresIn;
    
    if (isExpired) {
      delete this.cache[key];
      return null;
    }

    return entry.data as T;
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): void {
    delete this.cache[key];
  }

  clear(): void {
    this.cache = {};
  }

  // Método para fazer fetch com cache automático
  async fetchWithCache<T>(
    url: string, 
    options?: RequestInit,
    ttl: number = this.DEFAULT_TTL
  ): Promise<T> {
    const cacheKey = `${url}_${JSON.stringify(options || {})}`;
    
    // Verificar se existe no cache
    const cached = this.get<T>(cacheKey);
    if (cached) {
      console.log(`📦 Cache hit para: ${url}`);
      return cached;
    }

    console.log(`🌐 Buscando dados de: ${url}`);
    const startTime = Date.now();
    
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      
      const endTime = Date.now();
      console.log(`⏱️ Requisição ${url} levou ${endTime - startTime}ms`);
      
      // Salvar no cache
      this.set(cacheKey, data, ttl);
      
      return data;
    } catch (error) {
      console.error(`❌ Erro ao buscar ${url}:`, error);
      throw error;
    }
  }
}

// Instância singleton
export const apiCache = new ApiCache();

// Hook para usar o cache em componentes React
export function useApiCache() {
  return apiCache;
}
