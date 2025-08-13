"""
Endpoint DRE PostgreSQL Debug - Ultra Simples
"""
from fastapi import APIRouter, HTTPException
import pandas as pd

router = APIRouter()

@router.get("/dre-postgresql-debug")
async def get_dre_postgresql_debug():
    """Endpoint DRE PostgreSQL debug ultra-simples"""
    
    try:
        print("🔍 DRE PostgreSQL DEBUG - Iniciando")
        
        # 1. Testar importações básicas
        print("✅ Importações OK")
        
        # 2. Testar conexão com banco
        try:
            from database.connection_sqlalchemy import get_engine
            print("✅ Import get_engine OK")
            
            engine = get_engine()
            print("✅ Conexão com banco OK")
            
        except Exception as e:
            print(f"❌ Erro na conexão: {str(e)}")
            return {
                "success": False,
                "error": "conexao_banco",
                "message": str(e)
            }
        
        # 3. Testar consulta simples
        try:
            count_query = "SELECT COUNT(*) as total FROM financial_data"
            total_count = pd.read_sql(count_query, engine).iloc[0]['total']
            print(f"✅ Consulta COUNT OK: {total_count} registros")
            
        except Exception as e:
            print(f"❌ Erro na consulta COUNT: {str(e)}")
            return {
                "success": False,
                "error": "consulta_count",
                "message": str(e)
            }
        
        # 4. Testar consulta de colunas
        try:
            columns_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'financial_data'"
            columns = pd.read_sql(columns_query, engine)
            column_names = list(columns['column_name'])
            print(f"✅ Consulta colunas OK: {len(column_names)} colunas")
            print(f"   Colunas: {column_names[:10]}...")
            
        except Exception as e:
            print(f"❌ Erro na consulta colunas: {str(e)}")
            return {
                "success": False,
                "error": "consulta_colunas",
                "message": str(e)
            }
        
        # 5. Testar consulta DRE básica
        try:
            dre_query = """
            SELECT dre_n2, COUNT(*) as total
            FROM financial_data 
            WHERE dre_n2 IS NOT NULL AND dre_n2 != '' AND dre_n2 != 'nan'
            GROUP BY dre_n2
            LIMIT 5
            """
            dre_data = pd.read_sql(dre_query, engine)
            print(f"✅ Consulta DRE OK: {len(dre_data)} categorias")
            
            if not dre_data.empty:
                print("   Categorias encontradas:")
                for _, row in dre_data.iterrows():
                    print(f"     {row['dre_n2']}: {row['total']} registros")
            
        except Exception as e:
            print(f"❌ Erro na consulta DRE: {str(e)}")
            return {
                "success": False,
                "error": "consulta_dre",
                "message": str(e)
            }
        
        # 6. Retornar sucesso
        return {
            "success": True,
            "message": "Todos os testes passaram",
            "data": {
                "total_records": total_count,
                "columns_count": len(column_names),
                "columns": column_names,
                "dre_categories": len(dre_data),
                "dre_sample": dre_data.to_dict('records') if not dre_data.empty else []
            }
        }
        
    except Exception as e:
        print(f"❌ Erro geral no debug: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no debug: {str(e)}")
