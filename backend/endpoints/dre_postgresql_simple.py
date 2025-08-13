"""
Endpoint DRE PostgreSQL Simplificado - Com Debug Detalhado
"""
from fastapi import APIRouter, HTTPException
from database.connection_sqlalchemy import get_engine
import pandas as pd

router = APIRouter()

@router.get("/dre-postgresql-simple")
async def get_dre_postgresql_simple():
    """Endpoint DRE PostgreSQL simplificado com debug detalhado"""
    
    try:
        print("🔍 DRE PostgreSQL SIMPLIFICADO - Iniciando processamento")
        
        # 1. Conectar ao banco
        engine = get_engine()
        print("✅ Conexão com banco estabelecida")
        
        # 2. Verificar dados brutos primeiro
        print("\n📊 VERIFICANDO DADOS BRUTOS:")
        
        # Contar registros totais
        count_query = "SELECT COUNT(*) as total FROM financial_data"
        total_count = pd.read_sql(count_query, engine).iloc[0]['total']
        print(f"   Total de registros na tabela: {total_count}")
        
        # Verificar colunas disponíveis
        columns_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'financial_data'"
        columns = pd.read_sql(columns_query, engine)
        print(f"   Colunas disponíveis: {list(columns['column_name'])}")
        
        # Verificar dados com dre_n2
        dre_n2_query = """
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN dre_n2 IS NOT NULL THEN 1 END) as com_dre_n2,
               COUNT(CASE WHEN dre_n2 IS NULL THEN 1 END) as sem_dre_n2,
               COUNT(CASE WHEN dre_n2 = '' THEN 1 END) as dre_n2_vazio,
               COUNT(CASE WHEN dre_n2 = 'nan' THEN 1 END) as dre_n2_nan
        FROM financial_data
        """
        dre_n2_stats = pd.read_sql(dre_n2_query, engine).iloc[0]
        print(f"   Registros com dre_n2: {dre_n2_stats['com_dre_n2']}")
        print(f"   Registros sem dre_n2: {dre_n2_stats['sem_dre_n2']}")
        print(f"   Registros com dre_n2 vazio: {dre_n2_stats['dre_n2_vazio']}")
        print(f"   Registros com dre_n2 'nan': {dre_n2_stats['dre_n2_nan']}")
        
        # Verificar valores únicos de dre_n2
        dre_n2_unique_query = """
        SELECT dre_n2, COUNT(*) as total
        FROM financial_data 
        WHERE dre_n2 IS NOT NULL AND dre_n2 != '' AND dre_n2 != 'nan'
        GROUP BY dre_n2
        ORDER BY total DESC
        LIMIT 10
        """
        dre_n2_unique = pd.read_sql(dre_n2_unique_query, engine)
        print(f"   Top 10 categorias DRE N2:")
        for _, row in dre_n2_unique.iterrows():
            print(f"     {row['dre_n2']}: {row['total']} registros")
        
        # Verificar valores únicos de origem
        origem_query = """
        SELECT origem, COUNT(*) as total
        FROM financial_data 
        GROUP BY origem
        ORDER BY total DESC
        """
        origem_stats = pd.read_sql(origem_query, engine)
        print(f"   Distribuição por origem:")
        for _, row in origem_stats.iterrows():
            print(f"     {row['origem']}: {row['total']} registros")
        
        # Verificar valores únicos de valor_original
        valor_query = """
        SELECT 
            MIN(valor_original) as min_valor,
            MAX(valor_original) as max_valor,
            AVG(valor_original) as avg_valor,
            COUNT(CASE WHEN valor_original > 0 THEN 1 END) as receitas,
            COUNT(CASE WHEN valor_original < 0 THEN 1 END) as despesas,
            COUNT(CASE WHEN valor_original = 0 THEN 1 END) as zeros
        FROM financial_data 
        WHERE valor_original IS NOT NULL
        """
        valor_stats = pd.read_sql(valor_query, engine).iloc[0]
        print(f"   Estatísticas de valores:")
        print(f"     Mínimo: {valor_stats['min_valor']}")
        print(f"     Máximo: {valor_stats['max_valor']}")
        print(f"     Média: {valor_stats['avg_valor']}")
        print(f"     Receitas (>0): {valor_stats['receitas']}")
        print(f"     Despesas (<0): {valor_stats['despesas']}")
        print(f"     Zeros (=0): {valor_stats['zeros']}")
        
        # 3. Buscar dados reais para DRE
        print("\n📊 BUSCANDO DADOS REAIS PARA DRE:")
        
        dre_data_query = """
        SELECT 
            dre_n1, dre_n2, classificacao, valor_original, origem, competencia,
            CASE 
                WHEN valor_original > 0 THEN 'receita'
                ELSE 'despesa'
            END as type
        FROM financial_data 
        WHERE dre_n2 IS NOT NULL 
        AND dre_n2 != '' 
        AND dre_n2 != 'nan'
        AND valor_original IS NOT NULL
        AND competencia IS NOT NULL
        LIMIT 1000
        """
        
        df = pd.read_sql(dre_data_query, engine)
        print(f"   Dados carregados: {len(df)} registros")
        
        if df.empty:
            print("   ❌ Nenhum dado encontrado!")
            return {
                "success": True,
                "debug": {
                    "total_records": total_count,
                    "dre_n2_stats": dre_n2_stats.to_dict(),
                    "message": "Nenhum dado encontrado para DRE"
                },
                "meses": [],
                "trimestres": [],
                "anos": [],
                "data": []
            }
        
        # 4. Mostrar amostra dos dados
        print(f"   Amostra dos dados:")
        print(f"     Primeiras 5 linhas:")
        for i, row in df.head().iterrows():
            print(f"       {i}: {row['dre_n2']} | {row['valor_original']} | {row['origem']} | {row['competencia']}")
        
        # 5. Processar dados básicos
        print("\n📊 PROCESSANDO DADOS:")
        
        df['competencia'] = pd.to_datetime(df['competencia'], errors="coerce")
        df['mes_ano'] = df['competencia'].dt.to_period("M").astype(str)
        df['ano'] = df['competencia'].dt.year
        df['trimestre'] = df['competencia'].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")
        
        # Converter valor para numérico
        df['valor_original'] = pd.to_numeric(df['valor_original'], errors="coerce")
        df = df.dropna(subset=['competencia', 'valor_original'])
        
        # Períodos únicos
        meses_unicos = sorted(df['mes_ano'].dropna().unique())
        anos_unicos = sorted(set(int(a) for a in df['ano'].dropna().unique()))
        trimestres_unicos = sorted(df['trimestre'].dropna().unique())
        
        print(f"   Períodos encontrados:")
        print(f"     Meses: {meses_unicos[:5]}... (total: {len(meses_unicos)})")
        print(f"     Anos: {anos_unicos}")
        print(f"     Trimestres: {trimestres_unicos[:5]}... (total: {len(trimestres_unicos)})")
        
        # 6. Separar realizado e orçamento
        print("\n💰 SEPARANDO REALIZADO E ORÇAMENTO:")
        
        df_real = df[df['origem'] != "ORC"].copy()
        df_orc = df[df['origem'] == "ORC"].copy()
        
        print(f"   Realizado: {len(df_real)} registros")
        print(f"   Orçamento: {len(df_orc)} registros")
        
        if df_orc.empty:
            print("   ⚠️ Sem dados orçamentários, criando estrutura vazia")
            df_orc = df_real.copy()
            df_orc['valor_original'] = 0.0
            df_orc['origem'] = 'ORC'
        
        # 7. Calcular valores por categoria
        print("\n🧮 CALCULANDO VALORES POR CATEGORIA:")
        
        categorias_dre = df['dre_n2'].unique()
        print(f"   Categorias DRE N2 encontradas: {len(categorias_dre)}")
        
        result = []
        for categoria in categorias_dre[:5]:  # Limitar a 5 para debug
            print(f"   Processando categoria: {categoria}")
            
            df_cat_real = df_real[df_real['dre_n2'] == categoria]
            df_cat_orc = df_orc[df_orc['dre_n2'] == categoria]
            
            # Calcular valores por mês
            valores_mensais = {}
            orcamentos_mensais = {}
            
            for mes in meses_unicos[:3]:  # Limitar a 3 meses para debug
                df_mes_real = df_cat_real[df_cat_real['mes_ano'] == mes]
                df_mes_orc = df_cat_orc[df_cat_orc['mes_ano'] == mes]
                
                receitas_real = float(df_mes_real[df_mes_real['type'] == 'receita']['valor_original'].sum())
                despesas_real = float(df_mes_real[df_mes_real['type'] == 'despesa']['valor_original'].sum())
                valor_real = receitas_real - despesas_real
                
                receitas_orc = float(df_mes_orc[df_mes_orc['type'] == 'receita']['valor_original'].sum())
                despesas_orc = float(df_mes_orc[df_mes_orc['type'] == 'despesa']['valor_original'].sum())
                valor_orc = receitas_orc - despesas_orc
                
                valores_mensais[mes] = valor_real
                orcamentos_mensais[mes] = valor_orc
                
                print(f"     {mes}: Real={valor_real:.2f}, Orç={valor_orc:.2f}")
            
            # Criar item da categoria
            categoria_item = {
                "nome": categoria,
                "tipo": "+",  # Assumir positivo por padrão
                "valor": float(sum(valores_mensais.values())),
                "valores_mensais": valores_mensais,
                "valores_trimestrais": {tri: 0.0 for tri in trimestres_unicos[:3]},
                "valores_anuais": {str(ano): 0.0 for ano in anos_unicos},
                "orcamentos_mensais": orcamentos_mensais,
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres_unicos[:3]},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos_unicos},
                "orcamento_total": float(sum(orcamentos_mensais.values())),
                "classificacoes": []
            }
            
            result.append(categoria_item)
        
        # 8. Retornar resultado com debug
        return {
            "success": True,
            "debug": {
                "total_records": total_count,
                "dre_n2_stats": dre_n2_stats.to_dict(),
                "data_loaded": len(df),
                "realized_records": len(df_real),
                "budget_records": len(df_orc),
                "categories_found": len(categorias_dre),
                "periods": {
                    "months": len(meses_unicos),
                    "years": len(anos_unicos),
                    "quarters": len(trimestres_unicos)
                }
            },
            "meses": [str(mes) for mes in meses_unicos[:5]],
            "trimestres": [str(tri) for tri in trimestres_unicos[:5]],
            "anos": [str(ano) for ano in anos_unicos],
            "data": result
        }
        
    except Exception as e:
        print(f"❌ Erro no DRE PostgreSQL SIMPLIFICADO: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar DRE PostgreSQL: {str(e)}")
