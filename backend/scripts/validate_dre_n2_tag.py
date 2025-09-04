#!/usr/bin/env python3
"""
Script para validar valores DRE N2 TAG usando arquivo Excel de validação
Compara dados do Excel com os valores do banco PostgreSQL
"""

import pandas as pd
import sys
import os
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Tuple, Any
import json

# Adicionar o diretório backend ao path para importar módulos
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData, PlanoDeContas, DREStructureN2, DREStructureN0
from sqlalchemy import text

class DREValidator:
    def __init__(self, excel_file: str = "validacao dre grupo tag.xlsx"):
        self.excel_file = excel_file
        self.excel_data = None
        self.db_data = None
        self.discrepancies = []
        
    def load_excel_data(self) -> bool:
        """Carrega dados do arquivo Excel de validação"""
        try:
            excel_path = backend_path / self.excel_file
            if not excel_path.exists():
                print(f"❌ Arquivo Excel não encontrado: {excel_path}")
                return False
                
            print(f"📊 Carregando dados do Excel: {excel_path}")
            
            # Tentar ler todas as abas do Excel
            excel_file = pd.ExcelFile(excel_path)
            print(f"📋 Abas disponíveis: {excel_file.sheet_names}")
            
            # Carregar dados de todas as abas
            self.excel_data = {}
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    self.excel_data[sheet_name] = df
                    print(f"✅ Aba '{sheet_name}': {len(df)} linhas, {len(df.columns)} colunas")
                except Exception as e:
                    print(f"⚠️ Erro ao carregar aba '{sheet_name}': {e}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar arquivo Excel: {e}")
            return False
    
    def load_database_data(self) -> bool:
        """Carrega dados DRE N2 do banco PostgreSQL para TAG Business Solutions"""
        try:
            print("🗄️ Carregando dados do banco PostgreSQL...")
            
            with DatabaseSession() as session:
                # Query seguindo o fluxo: financial_data -> de_para -> plano_de_contas
                query = text("""
                    SELECT 
                        pc.classificacao_dre_n2 as dre_n2_name,
                        SUM(fd.valor) as total_valor,
                        COUNT(fd.id) as total_registros
                    FROM financial_data fd
                    JOIN de_para dp ON fd.de_para_id = dp.id
                    JOIN plano_de_contas pc ON dp.descricao_destino = pc.nome_conta
                    WHERE fd.empresa = 'TAG Business Solutions'
                    AND pc.classificacao_dre_n2 IS NOT NULL
                    AND pc.classificacao_dre_n2 != ''
                    GROUP BY pc.classificacao_dre_n2
                    ORDER BY pc.classificacao_dre_n2
                """)
                
                result = session.execute(query)
                self.db_data = []
                
                for row in result:
                    self.db_data.append({
                        'dre_n2_name': row.dre_n2_name,
                        'total_valor': float(row.total_valor) if row.total_valor else 0.0,
                        'total_registros': row.total_registros
                    })
                
                print(f"✅ Dados do banco carregados: {len(self.db_data)} contas DRE N2")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao carregar dados do banco: {e}")
            return False
    
    def analyze_excel_structure(self):
        """Analisa a estrutura do arquivo Excel"""
        if not self.excel_data:
            print("❌ Dados do Excel não carregados")
            return
            
        print("\n📊 ANÁLISE DA ESTRUTURA DO EXCEL:")
        print("=" * 50)
        
        for sheet_name, df in self.excel_data.items():
            print(f"\n📋 Aba: {sheet_name}")
            print(f"   Linhas: {len(df)}")
            print(f"   Colunas: {list(df.columns)}")
            
            # Mostrar primeiras linhas se houver dados
            if not df.empty:
                print(f"   Primeiras 3 linhas:")
                print(df.head(3).to_string())
            
            # Procurar por colunas relacionadas a DRE
            dre_columns = [col for col in df.columns if 'dre' in col.lower() or 'n2' in col.lower()]
            if dre_columns:
                print(f"   Colunas DRE encontradas: {dre_columns}")
    
    def compare_values(self):
        """Compara valores entre Excel e banco de dados"""
        if not self.excel_data or not self.db_data:
            print("❌ Dados não carregados para comparação")
            return
            
        print("\n🔍 COMPARAÇÃO DE VALORES:")
        print("=" * 50)
        
        # Procurar por dados de validação no Excel
        validation_data = None
        for sheet_name, df in self.excel_data.items():
            if 'dre' in sheet_name.lower() or 'n2' in sheet_name.lower() or 'tag' in sheet_name.lower():
                validation_data = df
                print(f"📊 Usando aba '{sheet_name}' para validação")
                break
        
        if validation_data is None:
            print("⚠️ Nenhuma aba específica de DRE encontrada, usando primeira aba com dados")
            validation_data = next(iter(self.excel_data.values()))
        
        # Comparar valores
        for db_item in self.db_data:
            dre_name = db_item['dre_n2_name']
            db_value = db_item['total_valor']
            
            # Procurar valor correspondente no Excel
            excel_value = self.find_excel_value(validation_data, dre_name)
            
            if excel_value is not None:
                difference = abs(db_value - excel_value)
                percentage_diff = (difference / abs(excel_value)) * 100 if excel_value != 0 else 0
                
                status = "✅" if percentage_diff < 1 else "⚠️" if percentage_diff < 5 else "❌"
                
                print(f"{status} {dre_name}")
                print(f"   Banco: R$ {db_value:,.2f}")
                print(f"   Excel: R$ {excel_value:,.2f}")
                print(f"   Diferença: R$ {difference:,.2f} ({percentage_diff:.2f}%)")
                
                if percentage_diff > 1:
                    self.discrepancies.append({
                        'conta': dre_name,
                        'banco_value': db_value,
                        'excel_value': excel_value,
                        'difference': difference,
                        'percentage_diff': percentage_diff
                    })
                print()
    
    def find_excel_value(self, df: pd.DataFrame, dre_name: str) -> float:
        """Encontra valor correspondente no Excel"""
        # Procurar por colunas que possam conter o nome da conta
        for col in df.columns:
            if df[col].dtype == 'object':  # Coluna de texto
                for idx, value in df[col].items():
                    if pd.notna(value) and dre_name.lower() in str(value).lower():
                        # Procurar valor numérico na mesma linha
                        for val_col in df.columns:
                            if df[val_col].dtype in ['int64', 'float64']:
                                val = df.iloc[idx][val_col]
                                if pd.notna(val) and val != 0:
                                    return float(val)
        return None
    
    def generate_report(self):
        """Gera relatório das discrepâncias encontradas"""
        if not self.discrepancies:
            print("\n✅ NENHUMA DISCREPÂNCIA SIGNIFICATIVA ENCONTRADA!")
            return
            
        print("\n📊 RELATÓRIO DE DISCREPÂNCIAS:")
        print("=" * 50)
        
        total_difference = sum(d['difference'] for d in self.discrepancies)
        
        print(f"🔍 Total de contas com discrepâncias: {len(self.discrepancies)}")
        print(f"💰 Diferença total: R$ {total_difference:,.2f}")
        print()
        
        for disc in sorted(self.discrepancies, key=lambda x: x['percentage_diff'], reverse=True):
            print(f"❌ {disc['conta']}")
            print(f"   Banco: R$ {disc['banco_value']:,.2f}")
            print(f"   Excel: R$ {disc['excel_value']:,.2f}")
            print(f"   Diferença: R$ {disc['difference']:,.2f} ({disc['percentage_diff']:.2f}%)")
            print()
    
    def save_report(self, filename: str = "dre_validation_report.json"):
        """Salva relatório em arquivo JSON"""
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'excel_file': self.excel_file,
            'total_discrepancies': len(self.discrepancies),
            'discrepancies': self.discrepancies,
            'db_data': self.db_data
        }
        
        report_path = backend_path / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {report_path}")

def main():
    """Função principal"""
    print("🔍 VALIDADOR DRE N2 TAG - INICIANDO")
    print("=" * 50)
    
    validator = DREValidator()
    
    # Carregar dados
    if not validator.load_excel_data():
        return
    
    if not validator.load_database_data():
        return
    
    # Analisar estrutura
    validator.analyze_excel_structure()
    
    # Comparar valores
    validator.compare_values()
    
    # Gerar relatório
    validator.generate_report()
    
    # Salvar relatório
    validator.save_report()
    
    print("\n✅ VALIDAÇÃO CONCLUÍDA!")

if __name__ == "__main__":
    main()
