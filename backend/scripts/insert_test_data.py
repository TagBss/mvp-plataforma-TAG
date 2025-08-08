#!/usr/bin/env python3
"""
Script para inserir dados de teste no PostgreSQL
"""
import sys
import os
from datetime import date, datetime
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData

def insert_test_data():
    """Insere dados de teste no banco"""
    
    test_data = [
        # Receitas - Janeiro 2024
        {
            'category': 'Vendas',
            'description': 'Vendas de produtos',
            'value': Decimal('50000.00'),
            'type': 'receita',
            'date': date(2024, 1, 15),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Serviços',
            'description': 'Consultoria',
            'value': Decimal('15000.00'),
            'type': 'receita',
            'date': date(2024, 1, 20),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        
        # Despesas - Janeiro 2024
        {
            'category': 'Salários',
            'description': 'Folha de pagamento',
            'value': Decimal('30000.00'),
            'type': 'despesa',
            'date': date(2024, 1, 5),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Aluguel',
            'description': 'Aluguel do escritório',
            'value': Decimal('8000.00'),
            'type': 'despesa',
            'date': date(2024, 1, 10),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Marketing',
            'description': 'Campanhas publicitárias',
            'value': Decimal('5000.00'),
            'type': 'despesa',
            'date': date(2024, 1, 25),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        
        # Receitas - Fevereiro 2024
        {
            'category': 'Vendas',
            'description': 'Vendas de produtos',
            'value': Decimal('55000.00'),
            'type': 'receita',
            'date': date(2024, 2, 15),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Serviços',
            'description': 'Consultoria',
            'value': Decimal('18000.00'),
            'type': 'receita',
            'date': date(2024, 2, 20),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        
        # Despesas - Fevereiro 2024
        {
            'category': 'Salários',
            'description': 'Folha de pagamento',
            'value': Decimal('32000.00'),
            'type': 'despesa',
            'date': date(2024, 2, 5),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Aluguel',
            'description': 'Aluguel do escritório',
            'value': Decimal('8000.00'),
            'type': 'despesa',
            'date': date(2024, 2, 10),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Marketing',
            'description': 'Campanhas publicitárias',
            'value': Decimal('6000.00'),
            'type': 'despesa',
            'date': date(2024, 2, 25),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        
        # Receitas - Março 2024
        {
            'category': 'Vendas',
            'description': 'Vendas de produtos',
            'value': Decimal('60000.00'),
            'type': 'receita',
            'date': date(2024, 3, 15),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Serviços',
            'description': 'Consultoria',
            'value': Decimal('20000.00'),
            'type': 'receita',
            'date': date(2024, 3, 20),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        
        # Despesas - Março 2024
        {
            'category': 'Salários',
            'description': 'Folha de pagamento',
            'value': Decimal('33000.00'),
            'type': 'despesa',
            'date': date(2024, 3, 5),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Aluguel',
            'description': 'Aluguel do escritório',
            'value': Decimal('8000.00'),
            'type': 'despesa',
            'date': date(2024, 3, 10),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
        {
            'category': 'Marketing',
            'description': 'Campanhas publicitárias',
            'value': Decimal('7000.00'),
            'type': 'despesa',
            'date': date(2024, 3, 25),
            'period': 'mensal',
            'source': 'Sistema ERP',
            'is_budget': False
        },
    ]
    
    try:
        with DatabaseSession() as session:
            # Limpar dados existentes (opcional)
            session.query(FinancialData).delete()
            session.commit()
            
            # Inserir dados de teste
            for data in test_data:
                financial_data = FinancialData(
                    category=data['category'],
                    description=data['description'],
                    value=data['value'],
                    type=data['type'],
                    date=data['date'],
                    period=data['period'],
                    source=data['source'],
                    is_budget=data['is_budget'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(financial_data)
            
            session.commit()
            print(f"✅ {len(test_data)} registros inseridos com sucesso!")
            
            # Verificar dados inseridos
            total_records = session.query(FinancialData).count()
            print(f"📊 Total de registros no banco: {total_records}")
            
            # Verificar por tipo
            receitas = session.query(FinancialData).filter(FinancialData.type == 'receita').count()
            despesas = session.query(FinancialData).filter(FinancialData.type == 'despesa').count()
            print(f"💰 Receitas: {receitas} registros")
            print(f"💸 Despesas: {despesas} registros")
            
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Inserindo dados de teste no PostgreSQL...")
    insert_test_data()
    print("✅ Script concluído!")
