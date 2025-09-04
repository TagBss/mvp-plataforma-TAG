# 🔴 Issue: Filtro Trimestral por Ano Específico

## 📝 **Descrição do Problema**

**Comportamento Atual:**
- ✅ **Todo período**: Filtro trimestral funciona e exibe dados corretamente
- ❌ **Ano específico**: Quando filtro por 2024 ou 2025, não retorna valores trimestrais

**Impacto:**
- Usuário não consegue visualizar dados trimestrais para anos específicos
- Funcionalidade de filtro por período fica incompleta
- Experiência do usuário prejudicada

## 🔍 **Dados de Teste Confirmados**

### **Backend API Status** ✅
```bash
Trimestres disponíveis: 10 trimestres
- Q1-2024, Q2-2024, Q3-2024, Q4-2024
- Q1-2025, Q2-2025, Q3-2025, Q4-2025  
- Q1-2026, Q2-2026

Exemplo Faturamento:
- Q1-2025: 561,585.69
- Q2-2025: 542,253.50
- Q3-2024: 10,498.27
- Q4-2024: 1,982.40
```

**Conclusão**: Backend retorna dados trimestrais corretamente para múltiplos anos.

## 🎯 **Causa Provável**

### **Hipótese 1: Problema no Frontend**
- Filtro frontend pode estar procurando formato incorreto
- Lógica de filtro por ano pode não estar aplicada aos trimestres
- JavaScript pode estar filtrando dados antes de exibir

### **Hipótese 2: Formato de Período**
- Backend retorna: `"Q1-2024"`, `"Q2-2025"`
- Frontend pode esperar: `"2024-Q1"` ou outro formato
- Incompatibilidade de formato causa dados não encontrados

### **Hipótese 3: Lógica de Agrupamento**
- Frontend pode estar agrupando por ano mas não aplicando aos trimestres
- Trimestres podem estar sendo tratados como categoria separada

## 🛠️ **Plano de Investigação**

### **Fase 1: Análise Frontend (30 min)**
1. **Localizar componente** que processa filtro trimestral
2. **Verificar função** de filtro por ano específico
3. **Comparar** com filtro mensal que funciona
4. **Identificar** onde a lógica diverge

### **Fase 2: Debug de Dados (15 min)**
1. **Console.log** dos dados antes e depois do filtro
2. **Verificar** se dados chegam corretos do backend
3. **Testar** filtros individuais (só trimestre, só ano)

### **Fase 3: Correção (30 min)**
1. **Corrigir** lógica de filtro identificada
2. **Testar** cenários: 2024, 2025, "todo período"
3. **Validar** que não quebrou outras funcionalidades

## 📋 **Checklist de Validação**

### **Para Implementar:**
- [ ] Localizar função de filtro trimestral no frontend
- [ ] Identificar diferença entre filtro mensal e trimestral
- [ ] Corrigir lógica de filtro por ano nos trimestres
- [ ] Testar filtro 2024 (deve exibir Q1-Q4 de 2024)
- [ ] Testar filtro 2025 (deve exibir Q1-Q3 de 2025)
- [ ] Testar "todo período" (deve exibir todos os trimestres)
- [ ] Verificar que valores estão corretos
- [ ] Confirmar que outros filtros não foram afetados

### **Casos de Teste:**
```javascript
// Teste 1: Todo período
filtro = { periodo: "trimestral", ano: "todos" }
// Esperado: Q1-2024, Q2-2024, Q3-2024, Q4-2024, Q1-2025, Q2-2025, Q3-2025, Q1-2026, Q2-2026

// Teste 2: Ano 2024
filtro = { periodo: "trimestral", ano: "2024" }
// Esperado: Q1-2024, Q2-2024, Q3-2024, Q4-2024

// Teste 3: Ano 2025  
filtro = { periodo: "trimestral", ano: "2025" }
// Esperado: Q1-2025, Q2-2025, Q3-2025, Q4-2025
```

## 🔧 **Comandos de Debug**

### **Backend - Confirmar Dados**
```bash
# Listar todos os trimestres
curl -s "http://localhost:8000/dre-n0/" | jq '.trimestres'

# Verificar valores de um trimestre específico
curl -s "http://localhost:8000/dre-n0/" | jq '.data[] | select(.nome | contains("Faturamento")) | .valores_trimestrais'
```

### **Frontend - Debug no Console**
```javascript
// No DevTools do browser
console.log("Dados do backend:", dadosRecebidos.trimestres);
console.log("Dados após filtro:", dadosFiltrados);
console.log("Filtro atual:", filtroAplicado);
```

## ⚡ **Prioridade**

**Alta** - Funcionalidade essencial para análise trimestral dos usuários

**Estimativa**: 1-2 horas de investigação e correção

**Complexidade**: Média (provavelmente lógica de filtro frontend)

---

**Criado em**: 2025-08-13  
**Status**: 🔴 **Pendente**  
**Responsável**: Frontend Developer  
**Relacionado**: DRE N0 Implementation (concluída)
