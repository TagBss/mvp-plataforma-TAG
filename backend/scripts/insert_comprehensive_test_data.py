#!/usr/bin/env python3
"""
Script para inserir dados de teste abrangentes no PostgreSQL
Cobre mais meses para simular dados similares aos do Excel
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData

def insert_comprehensive_test_data():
    """Insere dados de teste abrangentes no PostgreSQL"""
    
    # Dados de receitas por categoria
    receitas_data = [
        {"category": "Vendas", "description": "Vendas de produtos", "base_value": 50000},
        {"category": "Serviços", "description": "Consultoria", "base_value": 15000},
        {"category": "Licenciamentos", "description": "Licenças de software", "base_value": 8000},
        {"category": "Manutenção", "description": "Contratos de manutenção", "base_value": 12000},
        {"category": "Treinamentos", "description": "Cursos e treinamentos", "base_value": 6000},
    ]
    
    # Dados de despesas por categoria
    despesas_data = [
        {"category": "Salários", "description": "Folha de pagamento", "base_value": 35000},
        {"category": "Aluguel", "description": "Aluguel do escritório", "base_value": 8000},
        {"category": "Marketing", "description": "Publicidade e marketing", "base_value": 5000},
        {"category": "TI", "description": "Tecnologia da informação", "base_value": 3000},
        {"category": "Utilitários", "description": "Energia, água, internet", "base_value": 2000},
        {"category": "Seguros", "description": "Seguros empresariais", "base_value": 1500},
        {"category": "Impostos", "description": "Impostos e taxas", "base_value": 4000},
    ]
    
    # Gerar dados para 2024 (12 meses)
    test_data = []
    
    for month in range(1, 13):  # Janeiro a Dezembro
        # Receitas para este mês
        for receita in receitas_data:
            # Variação mensal de ±20%
            variation = random.uniform(0.8, 1.2)
            value = receita["base_value"] * variation
            
            test_data.append({
                "category": receita["category"],
                "description": receita["description"],
                "value": round(value, 2),
                "type": "receita",
                "date": f"2024-{month:02d}-15",  # Dia 15 de cada mês
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
        
        # Despesas para este mês
        for despesa in despesas_data:
            # Variação mensal de ±15%
            variation = random.uniform(0.85, 1.15)
            value = despesa["base_value"] * variation
            
            test_data.append({
                "category": despesa["category"],
                "description": despesa["description"],
                "value": round(value, 2),
                "type": "despesa",
                "date": f"2024-{month:02d}-15",  # Dia 15 de cada mês
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
    
    # Adicionar alguns dados de 2023 e 2025 para simular dados históricos e futuros
    # 2023 (últimos 3 meses)
    for month in range(10, 13):  # Outubro a Dezembro
        for receita in receitas_data[:3]:  # Apenas algumas receitas
            variation = random.uniform(0.7, 1.1)
            value = receita["base_value"] * variation
            
            test_data.append({
                "category": receita["category"],
                "description": receita["description"],
                "value": round(value, 2),
                "type": "receita",
                "date": f"2023-{month:02d}-15",
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
        
        for despesa in despesas_data[:3]:  # Apenas algumas despesas
            variation = random.uniform(0.8, 1.1)
            value = despesa["base_value"] * variation
            
            test_data.append({
                "category": despesa["category"],
                "description": despesa["description"],
                "value": round(value, 2),
                "type": "despesa",
                "date": f"2023-{month:02d}-15",
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
    
    # 2025 (primeiros 3 meses)
    for month in range(1, 4):  # Janeiro a Março
        for receita in receitas_data[:3]:  # Apenas algumas receitas
            variation = random.uniform(0.9, 1.3)
            value = receita["base_value"] * variation
            
            test_data.append({
                "category": receita["category"],
                "description": receita["description"],
                "value": round(value, 2),
                "type": "receita",
                "date": f"2025-{month:02d}-15",
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
        
        for despesa in despesas_data[:3]:  # Apenas algumas despesas
            variation = random.uniform(0.9, 1.2)
            value = despesa["base_value"] * variation
            
            test_data.append({
                "category": despesa["category"],
                "description": despesa["description"],
                "value": round(value, 2),
                "type": "despesa",
                "date": f"2025-{month:02d}-15",
                "period": "mensal",
                "source": "Sistema ERP",
                "is_budget": False
            })
    
    try:
        with DatabaseSession() as session:
            # Limpar dados existentes (opcional)
            session.query(FinancialData).delete()
            session.commit()
            
            # Inserir novos dados
            for data in test_data:
                financial_data = FinancialData(**data)
                session.add(financial_data)
            
            session.commit()
            
            print(f"✅ Dados inseridos com sucesso!")
            print(f"📊 Total de registros inseridos: {len(test_data)}")
            print(f"📅 Período coberto: 2023-10 a 2025-03")
            print(f"💰 Categorias de receita: {len(receitas_data)}")
            print(f"💸 Categorias de despesa: {len(despesas_data)}")
            
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    print("🚀 Iniciando inserção de dados de teste abrangentes...")
    insert_comprehensive_test_data()
    print("✅ Processo concluído!")
