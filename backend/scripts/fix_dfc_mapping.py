"""
Script para corrigir o mapeamento das categorias DFC no PostgreSQL
Atualiza as categorias dos dados reais com as informações de DFC do Excel
"""
import pandas as pd
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData

def fix_dfc_mapping():
    """Corrige o mapeamento de categorias para usar dados DFC"""
    
    print("🔧 Iniciando correção do mapeamento DFC...")
    
    try:
        # Carregar dados do Excel para obter o mapeamento correto
        excel_file = 'db_bluefit - Copia.xlsx'
        df_excel = pd.read_excel(excel_file, sheet_name='base')
        
        print(f"📂 Excel carregado: {len(df_excel)} registros")
        
        # Criar mapeamento baseado no índice (assumindo mesma ordem)
        # e usando apenas dados válidos (não fictícios)
        excel_mapping = []
        
        for index, row in df_excel.iterrows():
            excel_mapping.append({
                'index': index,
                'dfc_n1': str(row.get('dfc_n1', '')),
                'dfc_n2': str(row.get('dfc_n2', '')),
                'classificacao': str(row.get('classificacao', '')),
                'value': float(row.get('valor', 0)),
                'date': row.get('data')
            })
        
        # Atualizar registros no PostgreSQL
        updated_count = 0
        
        with DatabaseSession() as session:
            # Buscar apenas dados reais (não fictícios)
            real_data = session.query(FinancialData).filter(
                FinancialData.source != 'Sistema ERP'
            ).order_by(FinancialData.id).all()
            
            print(f"🔍 Dados reais encontrados: {len(real_data)}")
            
            # Atualizar cada registro com dados DFC corretos
            for i, record in enumerate(real_data):
                if i < len(excel_mapping):
                    excel_row = excel_mapping[i]
                    
                    # Determinar a categoria DFC prioritária
                    # Usar dfc_n2 se disponível, senão dfc_n1, senão classificacao
                    if excel_row['dfc_n2'] and excel_row['dfc_n2'] != 'nan':
                        new_category = excel_row['dfc_n2']
                    elif excel_row['dfc_n1'] and excel_row['dfc_n1'] != 'nan':
                        new_category = excel_row['dfc_n1']
                    else:
                        new_category = excel_row['classificacao']
                    
                    # Atualizar categoria se mudou
                    if record.category != new_category:
                        old_category = record.category
                        record.category = new_category
                        
                        updated_count += 1
                        
                        if updated_count <= 10:  # Mostrar apenas os primeiros 10
                            print(f"✅ ID {record.id}: '{old_category}' → '{new_category}'")
                        elif updated_count == 11:
                            print("... (mostrando apenas primeiros 10)")
                
                if updated_count % 100 == 0 and updated_count > 0:
                    print(f"📊 Atualizados: {updated_count} registros...")
            
            # Confirmar mudanças
            session.commit()
        
        print(f"✅ Correção concluída!")
        print(f"📊 Total atualizado: {updated_count} registros")
        
        # Verificar resultado
        verify_dfc_mapping()
        
    except Exception as e:
        print(f"❌ Erro na correção: {e}")
        raise

def verify_dfc_mapping():
    """Verifica se a correção foi aplicada corretamente"""
    
    print("\n🔍 Verificando correção...")
    
    with DatabaseSession() as session:
        # Contar categorias com operadores DFC
        real_data = session.query(FinancialData).filter(
            FinancialData.source != 'Sistema ERP'
        ).all()
        
        categorias_com_operadores = 0
        categorias_unicas = set()
        
        for record in real_data:
            if record.category and ('(' in record.category and ')' in record.category):
                categorias_com_operadores += 1
                categorias_unicas.add(record.category)
        
        print(f"📊 Registros com categorias DFC: {categorias_com_operadores}/{len(real_data)}")
        print(f"📋 Categorias DFC únicas: {len(categorias_unicas)}")
        
        if categorias_unicas:
            print("🎯 Exemplos de categorias DFC:")
            for i, categoria in enumerate(list(categorias_unicas)[:10]):
                print(f"  {i+1}. \"{categoria}\"")

if __name__ == "__main__":
    fix_dfc_mapping()
