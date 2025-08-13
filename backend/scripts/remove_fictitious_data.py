"""
Script para remover definitivamente os dados fictícios do PostgreSQL
Remove todos os registros com source = "Sistema ERP"
"""
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData

def remove_fictitious_data():
    """Remove dados fictícios do banco PostgreSQL"""
    
    print("🧹 Iniciando remoção de dados fictícios...")
    
    try:
        with DatabaseSession() as session:
            # Contar registros fictícios antes da remoção
            count_before = session.query(FinancialData).filter(
                FinancialData.source == 'Sistema ERP'
            ).count()
            
            print(f"📊 Registros fictícios encontrados: {count_before}")
            
            if count_before == 0:
                print("✅ Nenhum dado fictício encontrado!")
                return
            
            # Buscar alguns exemplos antes de remover
            exemplos = session.query(FinancialData).filter(
                FinancialData.source == 'Sistema ERP'
            ).limit(5).all()
            
            print("🔍 Exemplos de registros fictícios:")
            for record in exemplos:
                print(f"  ID {record.id}: {record.category} - {record.value} - {record.created_at}")
            
            # Confirmar remoção
            print(f"\\n⚠️  ATENÇÃO: Serão removidos {count_before} registros fictícios!")
            print("Esta operação é irreversível.")
            
            # Remover todos os registros fictícios
            deleted_count = session.query(FinancialData).filter(
                FinancialData.source == 'Sistema ERP'
            ).delete()
            
            # Confirmar transação
            session.commit()
            
            print(f"✅ Remoção concluída!")
            print(f"📊 Registros removidos: {deleted_count}")
            
            # Verificar contagem final
            count_after = session.query(FinancialData).count()
            print(f"📊 Total de registros restantes: {count_after}")
            
            # Verificar se ainda há dados fictícios
            remaining_fictitious = session.query(FinancialData).filter(
                FinancialData.source == 'Sistema ERP'
            ).count()
            
            if remaining_fictitious == 0:
                print("✅ Todos os dados fictícios foram removidos com sucesso!")
            else:
                print(f"⚠️  Ainda restam {remaining_fictitious} registros fictícios")
                
    except Exception as e:
        print(f"❌ Erro na remoção: {e}")
        raise

def verify_clean_data():
    """Verifica se os dados estão limpos após a remoção"""
    
    print("\\n🔍 Verificando limpeza dos dados...")
    
    with DatabaseSession() as session:
        # Contar total de registros
        total_records = session.query(FinancialData).count()
        
        # Contar registros por fonte
        sources = session.query(FinancialData.source, session.query(FinancialData).filter(
            FinancialData.source == FinancialData.source
        ).count().label('count')).group_by(FinancialData.source).all()
        
        print(f"📊 Total de registros: {total_records}")
        print("📋 Registros por fonte:")
        
        for source, count in sources:
            print(f"  - {source}: {count} registros")
        
        # Verificar se há registros com operadores DFC
        records_with_operators = session.query(FinancialData).filter(
            FinancialData.category.like('%( % )%')
        ).count()
        
        print(f"🎯 Registros com operadores DFC: {records_with_operators}")
        
        # Mostrar alguns exemplos de categorias DFC
        dfc_examples = session.query(FinancialData.category).filter(
            FinancialData.category.like('%( % )%')
        ).distinct().limit(10).all()
        
        if dfc_examples:
            print("\\n📋 Exemplos de categorias DFC:")
            for i, (category,) in enumerate(dfc_examples, 1):
                print(f"  {i}. \"{category}\"")

if __name__ == "__main__":
    remove_fictitious_data()
    verify_clean_data()
