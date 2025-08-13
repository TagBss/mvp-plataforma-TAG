"""
Endpoint DRE PostgreSQL - Baseado na versão Excel que funciona
"""
from fastapi import APIRouter, HTTPException
from database.repository_sqlalchemy import FinancialDataRepository
from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import DREStructureN1, DREStructureN2, DREClassification
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import Dict, List, Any

router = APIRouter()

@router.get("/dre-postgresql")
async def get_dre_postgresql():
    """Endpoint DRE PostgreSQL baseado na versão Excel"""
    
    try:
        print("🔍 DRE PostgreSQL - Iniciando processamento")
        
        # 1. Conectar ao banco e buscar dados
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Buscar dados financeiros da tabela financial_data
            query = """
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
            """
            
            df = pd.read_sql(query, engine)
            print(f"📊 Dados carregados: {len(df)} registros")
            
            if df.empty:
                return {
                    "success": True,
                    "meses": [],
                    "trimestres": [],
                    "anos": [],
                    "data": []
                }
            
            # 2. Processar dados como na versão Excel
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
            
            print(f"📅 Períodos: {meses_unicos[:5]}... (total: {len(meses_unicos)})")
            print(f"🏷️ Categorias DRE N2: {df['dre_n2'].unique()[:10]}... (total: {len(df['dre_n2'].unique())})")
            
            # 3. Separar realizado e orçamento (como na versão Excel)
            df_real = df[df['origem'] != "ORC"].copy()
            df_orc = df[df['origem'] == "ORC"].copy()
            
            if df_orc.empty:
                # Criar DataFrame vazio com a mesma estrutura
                df_orc = df_real.copy()
                df_orc['valor_original'] = 0.0
                df_orc['origem'] = 'ORC'
            
            print(f"💰 Realizado: {len(df_real)} registros, Orçamento: {len(df_orc)} registros")
            
            # 4. Buscar estruturas DRE do banco
            dre_n1_items = session.query(DREStructureN1).order_by(DREStructureN1.order_index).all()
            dre_n2_items = session.query(DREStructureN2).order_by(DREStructureN2.order_index).all()
            
            print(f"🏗️ Estruturas DRE N1: {len(dre_n1_items)}")
            print(f"🏗️ Estruturas DRE N2: {len(dre_n2_items)}")
            
            if not dre_n1_items:
                # Estrutura básica se não houver estruturas migradas
                return await get_dre_basic_structure(df, meses_unicos, trimestres_unicos, anos_unicos)
            
            # 5. Calcular totais por período (como na versão Excel)
            totais = calcular_totais_por_periodo_postgresql(
                df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos
            )
            
            # 6. Criar estrutura DRE baseada nas estruturas migradas
            result = []
            
            for totalizador_n1 in dre_n1_items:
                totalizador_item = {
                    "nome": totalizador_n1.name,
                    "tipo": totalizador_n1.operation_type,
                    "valor": 0.0,
                    "valores_mensais": {mes: 0.0 for mes in meses_unicos},
                    "valores_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                    "valores_anuais": {str(ano): 0.0 for ano in anos_unicos},
                    "orcamentos_mensais": {mes: 0.0 for mes in meses_unicos},
                    "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                    "orcamentos_anuais": {str(ano): 0.0 for ano in anos_unicos},
                    "orcamento_total": 0.0,
                    "classificacoes": []
                }
                
                # Buscar contas DRE N2 filhas deste totalizador
                contas_n2 = [item for item in dre_n2_items if item.dre_n1_id == totalizador_n1.dre_n1_id]
                
                for conta_n2 in contas_n2:
                    conta_n2_item = {
                        "nome": conta_n2.name,
                        "tipo": conta_n2.operation_type,
                        "valor": 0.0,
                        "valores_mensais": {mes: 0.0 for mes in meses_unicos},
                        "valores_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                        "valores_anuais": {str(ano): 0.0 for ano in anos_unicos},
                        "orcamentos_mensais": {mes: 0.0 for mes in meses_unicos},
                        "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                        "orcamentos_anuais": {str(ano): 0.0 for ano in anos_unicos},
                        "orcamento_total": 0.0,
                        "classificacoes": []
                    }
                    
                    # Buscar dados financeiros para esta conta DRE N2
                    df_conta_real = df_real[df_real['dre_n2'] == conta_n2.name]
                    df_conta_orc = df_orc[df_orc['dre_n2'] == conta_n2.name]
                    
                    if not df_conta_real.empty:
                        # Calcular valores por período para a conta
                        for mes in meses_unicos:
                            df_mes_real = df_conta_real[df_conta_real['mes_ano'] == mes]
                            df_mes_orc = df_conta_orc[df_conta_orc['mes_ano'] == mes]
                            
                            # Realizado
                            receitas_mes_real = float(df_mes_real[df_mes_real['type'] == 'receita']['valor_original'].sum())
                            despesas_mes_real = float(df_mes_real[df_mes_real['type'] == 'despesa']['valor_original'].sum())
                            valor_mes_real = receitas_mes_real - despesas_mes_real
                            
                            # Orçamento
                            receitas_mes_orc = float(df_mes_orc[df_mes_orc['type'] == 'receita']['valor_original'].sum())
                            despesas_mes_orc = float(df_mes_orc[df_mes_orc['type'] == 'despesa']['valor_original'].sum())
                            valor_mes_orc = receitas_mes_orc - despesas_mes_orc
                            
                            # Aplicar operador matemático
                            if conta_n2.operation_type == '+':
                                valor_mes_real = abs(valor_mes_real)
                                valor_mes_orc = abs(valor_mes_orc)
                            elif conta_n2.operation_type == '-':
                                valor_mes_real = -abs(valor_mes_real)
                                valor_mes_orc = -abs(valor_mes_orc)
                            
                            conta_n2_item["valores_mensais"][mes] = valor_mes_real
                            conta_n2_item["orcamentos_mensais"][mes] = valor_mes_orc
                            totalizador_item["valores_mensais"][mes] += valor_mes_real
                            totalizador_item["orcamentos_mensais"][mes] += valor_mes_orc
                        
                        # Calcular valor total da conta
                        conta_n2_item["valor"] = float(sum(conta_n2_item["valores_mensais"].values()))
                        conta_n2_item["orcamento_total"] = float(sum(conta_n2_item["orcamentos_mensais"].values()))
                        
                        # Buscar classificações específicas para esta conta
                        classificacoes = session.query(DREClassification).filter(
                            DREClassification.dre_n2_id == conta_n2.dre_n2_id
                        ).all()
                        
                        for classificacao in classificacoes:
                            classificacao_item = {
                                "nome": classificacao.name,
                                "valor": 0.0,
                                "valores_mensais": {mes: 0.0 for mes in meses_unicos},
                                "valores_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                                "valores_anuais": {str(ano): 0.0 for ano in anos_unicos},
                                "orcamentos_mensais": {mes: 0.0 for mes in meses_unicos},
                                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres_unicos},
                                "orcamentos_anuais": {str(ano): 0.0 for ano in anos_unicos}
                            }
                            
                            # Calcular valores para classificação
                            df_class_real = df_conta_real[df_conta_real['classificacao'] == classificacao.name]
                            df_class_orc = df_conta_orc[df_conta_orc['classificacao'] == classificacao.name]
                            
                            for mes in meses_unicos:
                                df_class_mes_real = df_class_real[df_class_real['mes_ano'] == mes]
                                df_class_mes_orc = df_class_orc[df_class_orc['mes_ano'] == mes]
                                
                                receitas_mes_real = float(df_class_mes_real[df_class_mes_real['type'] == 'receita']['valor_original'].sum())
                                despesas_mes_real = float(df_class_mes_real[df_class_mes_real['type'] == 'despesa']['valor_original'].sum())
                                valor_mes_real = receitas_mes_real - despesas_mes_real
                                
                                receitas_mes_orc = float(df_class_mes_orc[df_class_mes_orc['type'] == 'receita']['valor_original'].sum())
                                despesas_mes_orc = float(df_class_mes_orc[df_class_mes_orc['type'] == 'despesa']['valor_original'].sum())
                                valor_mes_orc = receitas_mes_orc - despesas_mes_orc
                                
                                if conta_n2.operation_type == '+':
                                    valor_mes_real = abs(valor_mes_real)
                                    valor_mes_orc = abs(valor_mes_orc)
                                elif conta_n2.operation_type == '-':
                                    valor_mes_real = -abs(valor_mes_real)
                                    valor_mes_orc = -abs(valor_mes_orc)
                                
                                classificacao_item["valores_mensais"][mes] = valor_mes_real
                                classificacao_item["orcamentos_mensais"][mes] = valor_mes_orc
                            
                            conta_n2_item["classificacoes"].append(classificacao_item)
                    
                    # Adicionar conta DRE N2 como classificação do totalizador
                    totalizador_item["classificacoes"].append(conta_n2_item)
                
                # Calcular valor total do totalizador
                totalizador_item["valor"] = float(sum(totalizador_item["valores_mensais"].values()))
                totalizador_item["orcamento_total"] = float(sum(totalizador_item["orcamentos_mensais"].values()))
                
                # Adicionar totalizador ao resultado
                result.append(totalizador_item)
            
            # 7. Preparar dados de orçamento por período (como na versão Excel)
            orcamentos_mensais = {
                mes: {item["nome"]: item["orcamentos_mensais"].get(mes, 0.0) for item in result}
                for mes in meses_unicos
            }
            
            orcamentos_trimestrais = {
                tri: {item["nome"]: item["orcamentos_trimestrais"].get(tri, 0.0) for item in result}
                for tri in trimestres_unicos
            }
            
            orcamentos_anuais = {
                str(ano): {item["nome"]: item["orcamentos_anuais"].get(str(ano), 0.0) for item in result}
                for ano in anos_unicos
            }
            
            orcamentos_totais = {item["nome"]: item["orcamento_total"] for item in result}
            
            return {
                "success": True,
                "meses": [str(mes) for mes in meses_unicos],
                "trimestres": [str(tri) for tri in trimestres_unicos],
                "anos": [str(ano) for ano in anos_unicos],
                "data": result,
                "orcamentos_mensais": orcamentos_mensais,
                "orcamentos_trimestrais": orcamentos_trimestrais,
                "orcamentos_anuais": orcamentos_anuais,
                "orcamento_total": orcamentos_totais
            }
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Erro no DRE PostgreSQL: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar DRE PostgreSQL: {str(e)}")

async def get_dre_basic_structure(df, meses, trimestres, anos):
    """Estrutura DRE básica quando não há estruturas migradas"""
    # Calcular valores reais dos dados
    receitas_total = float(df[df['type'] == 'receita']['valor_original'].sum())
    despesas_total = float(df[df['type'] == 'despesa']['valor_original'].sum())
    
    # Calcular valores por período
    receitas_mensais = {}
    despesas_mensais = {}
    for mes in meses:
        df_mes = df[df['mes_ano'] == mes]
        receitas_mensais[mes] = float(df_mes[df_mes['type'] == 'receita']['valor_original'].sum())
        despesas_mensais[mes] = float(df_mes[df_mes['type'] == 'despesa']['valor_original'].sum())
    
    return {
        "success": True,
        "meses": [str(mes) for mes in meses],
        "trimestres": [str(tri) for tri in trimestres],
        "anos": [str(ano) for ano in anos],
        "data": [
            {
                "nome": "Receitas",
                "tipo": "+",
                "valor": receitas_total,
                "valores_mensais": receitas_mensais,
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "orcamento_total": 0.0,
                "classificacoes": []
            },
            {
                "nome": "Despesas",
                "tipo": "-",
                "valor": despesas_total,
                "valores_mensais": despesas_mensais,
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "orcamento_total": 0.0,
                "classificacoes": []
            }
        ],
        "orcamentos_mensais": {mes: {"Receitas": 0.0, "Despesas": 0.0} for mes in meses},
        "orcamentos_trimestrais": {tri: {"Receitas": 0.0, "Despesas": 0.0} for tri in trimestres},
        "orcamentos_anuais": {str(ano): {"Receitas": 0.0, "Despesas": 0.0} for ano in anos},
        "orcamento_total": {"Receitas": 0.0, "Despesas": 0.0}
    }

def calcular_totais_por_periodo_postgresql(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos):
    """Calcula totais por período para realizado e orçamento (como na versão Excel)"""
    
    # Realizado
    total_real_por_mes = {
        mes: df_real[df_real["mes_ano"] == mes].groupby("dre_n2")["valor_original"].sum().to_dict()
        for mes in meses_unicos
    }
    
    # Orçamento
    total_orc_por_mes = {
        mes: df_orc[df_orc["mes_ano"] == mes].groupby("dre_n2")["valor_original"].sum().to_dict()
        for mes in meses_unicos
    }
    
    # Trimestres
    total_real_por_tri = {}
    total_orc_por_tri = {}
    
    for tri in trimestres_unicos:
        meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
        soma_real = {}
        soma_orc = {}
        for mes in meses_do_tri:
            for conta, valor in total_real_por_mes.get(mes, {}).items():
                soma_real[conta] = soma_real.get(conta, 0) + valor
            for conta, valor in total_orc_por_mes.get(mes, {}).items():
                soma_orc[conta] = soma_orc.get(conta, 0) + valor
        total_real_por_tri[tri] = soma_real
        total_orc_por_tri[tri] = soma_orc
    
    # Anos
    total_real_por_ano = {}
    total_orc_por_ano = {}
    for ano in anos_unicos:
        meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
        soma_real = {}
        soma_orc = {}
        for mes in meses_do_ano:
            for conta, valor in total_real_por_mes.get(mes, {}).items():
                soma_real[conta] = soma_real.get(conta, 0) + valor
            for conta, valor in total_orc_por_mes.get(mes, {}).items():
                soma_orc[conta] = soma_orc.get(conta, 0) + valor
        total_real_por_ano[ano] = soma_real
        total_orc_por_ano[ano] = soma_orc
    
    # Totais gerais
    total_geral_real = {}
    total_geral_orc = {}
    for mes in meses_unicos:
        if mes in total_real_por_mes:
            for conta, valor in total_real_por_mes[mes].items():
                total_geral_real[conta] = total_geral_real.get(conta, 0) + valor
        if mes in total_orc_por_mes:
            for conta, valor in total_orc_por_mes[mes].items():
                total_geral_orc[conta] = total_geral_orc.get(conta, 0) + valor
    
    return {
        'total_real_por_mes': total_real_por_mes,
        'total_orc_por_mes': total_orc_por_mes,
        'total_real_por_tri': total_real_por_tri,
        'total_orc_por_tri': total_orc_por_tri,
        'total_real_por_ano': total_real_por_ano,
        'total_orc_por_ano': total_orc_por_ano,
        'total_geral_real': total_geral_real,
        'total_geral_orc': total_geral_orc
    }
