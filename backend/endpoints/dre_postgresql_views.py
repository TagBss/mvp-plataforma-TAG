"""
Endpoint DRE PostgreSQL - Consumindo Views SQL
"""
from fastapi import APIRouter, HTTPException
from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
import pandas as pd
from typing import List, Dict, Any

router = APIRouter()

@router.get("/dre-postgresql-views")
async def get_dre_postgresql_views():
    """Endpoint DRE consumindo views SQL do PostgreSQL"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            
            # 2. Buscar dados diretamente da tabela financial_data
            dre_query = """
            SELECT 
                dre_n2,
                dre_n1,
                classificacao,
                valor_original as resultado_mes,
                valor_original as resultado_trimestre,
                valor_original as resultado_ano,
                0 as resultado_orc_mes,
                0 as resultado_orc_trimestre,
                0 as resultado_orc_ano,
                TO_CHAR(competencia, 'YYYY-MM') as mes_ano,
                CONCAT(EXTRACT(YEAR FROM competencia), '-T', EXTRACT(QUARTER FROM competencia)) as trimestre,
                EXTRACT(YEAR FROM competencia) as ano,
                empresa
            FROM financial_data 
            WHERE dre_n2 IS NOT NULL 
            AND dre_n2 != '' 
            AND dre_n2 != 'nan'
            AND valor_original IS NOT NULL
            AND competencia IS NOT NULL
            ORDER BY dre_n2, competencia;
            """
            
            df = pd.read_sql(dre_query, connection)
            
            if df.empty:
                raise HTTPException(status_code=404, detail="Nenhum dado encontrado para DRE")
            
            # 3. Processar dados para o formato esperado pelo frontend
            # Agrupar por categoria DRE
            categorias_dre = df['dre_n2'].unique()
            
            # Períodos únicos
            meses_unicos = sorted(df['mes_ano'].dropna().unique())
            trimestres_unicos = sorted(df['trimestre'].dropna().unique())
            anos_unicos = sorted(set(int(a) for a in df['ano'].dropna().unique()))
            
            # Estrutura para o frontend
            estrutura_dre = []
            
            for categoria in categorias_dre:
                df_cat = df[df['dre_n2'] == categoria]
                
                # Valores por mês
                valores_mensais = {}
                orcamentos_mensais = {}
                for mes in meses_unicos:
                    df_mes = df_cat[df_cat['mes_ano'] == mes]
                    valores_mensais[mes] = float(df_mes['resultado_mes'].sum())
                    orcamentos_mensais[mes] = float(df_mes['resultado_orc_mes'].sum())
                
                # Valores por trimestre
                valores_trimestrais = {}
                orcamentos_trimestrais = {}
                for tri in trimestres_unicos:
                    df_tri = df_cat[df_cat['trimestre'] == tri]
                    valores_trimestrais[tri] = float(df_tri['resultado_trimestre'].sum())
                    orcamentos_trimestrais[tri] = float(df_tri['resultado_orc_trimestre'].sum())
                
                # Valores por ano
                valores_anuais = {}
                orcamentos_anuais = {}
                for ano in anos_unicos:
                    df_ano = df_cat[df_cat['ano'] == ano]
                    valores_anuais[str(ano)] = float(df_ano['resultado_ano'].sum())
                    orcamentos_anuais[str(ano)] = float(df_ano['resultado_orc_ano'].sum())
                
                # Determinar tipo baseado no valor total
                total_categoria = sum(valores_mensais.values())
                tipo = "+" if total_categoria > 0 else "-"
                
                # Criar item da categoria
                categoria_item = {
                    "nome": categoria,
                    "tipo": tipo,
                    "valor": total_categoria,
                    "valores_mensais": valores_mensais,
                    "valores_trimestrais": valores_trimestrais,
                    "valores_anuais": valores_anuais,
                    "orcamentos_mensais": orcamentos_mensais,
                    "orcamentos_trimestrais": orcamentos_trimestrais,
                    "orcamentos_anuais": orcamentos_anuais,
                    "orcamento_total": sum(orcamentos_mensais.values()),
                    "expandivel": False,  # Por enquanto, sem classificações
                    "classificacoes": []
                }
                
                estrutura_dre.append(categoria_item)
            
            # 4. Retornar dados no formato esperado pelo frontend
            return {
                "success": True,
                "meses": [str(mes) for mes in meses_unicos],
                "trimestres": [str(tri) for tri in trimestres_unicos],
                "anos": anos_unicos,
                "data": estrutura_dre,
                "source": "PostgreSQL Direct Query",
                "total_categorias": len(estrutura_dre)
            }
            
    except Exception as e:
        print(f"❌ Erro no DRE PostgreSQL Views: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar DRE PostgreSQL: {str(e)}")

@router.get("/dre-postgresql-views/structure")
async def get_dre_structure():
    """Retorna a estrutura das views DRE disponíveis"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Verificar views disponíveis
            views_query = """
            SELECT 
                viewname,
                definition
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname LIKE 'v_dre%'
            ORDER BY viewname;
            """
            
            views_result = connection.execute(text(views_query))
            views = [{"name": row[0], "definition": row[1]} for row in views_result.fetchall()]
            
            return {
                "success": True,
                "views": views,
                "total_views": len(views)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estrutura: {str(e)}")
