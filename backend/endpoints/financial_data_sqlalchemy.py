"""
Endpoints para dados financeiros usando PostgreSQL e SQLAlchemy
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from decimal import Decimal
import pandas as pd

from database.repository_sqlalchemy import FinancialDataRepository
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import DFCStructureN1, DFCStructureN2, DFCClassification

router = APIRouter(prefix="/financial-data", tags=["Financial Data"])

# Pydantic models
class FinancialDataCreate(BaseModel):
    category: str
    description: Optional[str] = None
    value: float
    type: str  # 'receita', 'despesa', 'investimento'
    date: date
    period: Optional[str] = 'mensal'
    source: Optional[str] = None
    is_budget: bool = False

class FinancialDataUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    type: Optional[str] = None
    date: Optional[date] = None
    period: Optional[str] = None
    source: Optional[str] = None
    is_budget: Optional[bool] = None

class FinancialDataResponse(BaseModel):
    id: int
    category: str
    description: Optional[str]
    value: float
    type: str
    date: date
    period: Optional[str]
    source: Optional[str]
    is_budget: bool
    created_at: datetime
    updated_at: datetime

# Dependency
def get_financial_repository() -> FinancialDataRepository:
    return FinancialDataRepository()

# Importar funções dos helpers PostgreSQL
from helpers_postgresql.data_processor_postgresql import calcular_mom_postgresql, calcular_pmr_pmp_postgresql

@router.get("/", response_model=List[FinancialDataResponse])
async def get_financial_data(
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    category: Optional[str] = Query(None, description="Categoria"),
    data_type: Optional[str] = Query(None, description="Tipo de dado"),
    is_budget: Optional[bool] = Query(None, description="Se é orçado"),
    limit: int = Query(100000, description="Limite de registros"),
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Busca dados financeiros com filtros"""
    
    try:
        data = repository.get_financial_data(
            start_date=start_date,
            end_date=end_date,
            category=category,
            data_type=data_type,
            is_budget=is_budget,
            limit=limit
        )
        
        return [FinancialDataResponse(**item) for item in data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")

@router.get("/by-period")
async def get_data_by_period(
    period_type: str = Query(..., description="Tipo de período (month, quarter, year)"),
    start_date: date = Query(..., description="Data inicial"),
    end_date: date = Query(..., description="Data final"),
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Busca dados agrupados por período"""
    
    try:
        data = repository.get_data_by_period(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period_type": period_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados por período: {str(e)}")

@router.get("/summary")
async def get_summary_by_type(
    start_date: date = Query(..., description="Data inicial"),
    end_date: date = Query(..., description="Data final"),
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Busca resumo por tipo de dado financeiro"""
    
    try:
        summary = repository.get_summary_by_type(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")

@router.get("/categories")
async def get_categories_hierarchy(
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Busca hierarquia de categorias"""
    
    try:
        categories = repository.get_categories_hierarchy()
        return {"categories": categories}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar categorias: {str(e)}")

@router.get("/months")
async def get_available_months(
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Busca meses disponíveis nos dados"""
    
    try:
        months = repository.get_available_months()
        return {"meses_disponiveis": months}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar meses: {str(e)}")

@router.post("/", response_model=FinancialDataResponse)
async def create_financial_data(
    data: FinancialDataCreate,
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Cria novo registro financeiro"""
    
    try:
        data_dict = data.dict()
        data_dict["created_at"] = datetime.now()
        data_dict["updated_at"] = datetime.now()
        
        new_id = repository.insert_financial_data(data_dict)
        
        # Buscar o registro criado
        created_data = repository.get_financial_data(limit=1)
        if created_data:
            return FinancialDataResponse(**created_data[0])
        
        raise HTTPException(status_code=500, detail="Erro ao criar registro")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar dados: {str(e)}")

@router.put("/{data_id}", response_model=FinancialDataResponse)
async def update_financial_data(
    data_id: int,
    data: FinancialDataUpdate,
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Atualiza registro financeiro existente"""
    
    try:
        data_dict = data.dict(exclude_unset=True)
        data_dict["updated_at"] = datetime.now()
        
        success = repository.update_financial_data(data_id, data_dict)
        
        if not success:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        
        # Buscar o registro atualizado
        updated_data = repository.get_financial_data(limit=1)
        if updated_data:
            return FinancialDataResponse(**updated_data[0])
        
        raise HTTPException(status_code=500, detail="Erro ao atualizar registro")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar dados: {str(e)}")

@router.delete("/{data_id}")
async def delete_financial_data(
    data_id: int,
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Remove registro financeiro"""
    
    try:
        success = repository.delete_financial_data(data_id)
        if not success:
            raise HTTPException(status_code=404, detail="Registro não encontrado")
        
        return {"message": "Registro removido com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover dados: {str(e)}")

@router.get("/health")
async def health_check():
    """Verifica saúde do sistema"""
    
    try:
        repository = FinancialDataRepository()
        # Testar conexão com banco
        data = repository.get_financial_data(limit=1)
        
        return {
            "status": "healthy",
            "database_connected": True,
            "records_count": len(data) if data else 0,
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.now()
        }

@router.get("/receber")
async def get_receber_saldo(
    mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM"),
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Endpoint para contas a receber - compatível com versão Excel"""
    
    try:
        # Definir período baseado no filtro de mês
        if mes:
            # Parse do mês YYYY-MM
            year, month = map(int, mes.split('-'))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            # Todo o período disponível
            start_date = date(2020, 1, 1)  # Data mínima
            end_date = date(2030, 12, 31)  # Data máxima
        
        # Buscar dados de receita
        data = repository.get_financial_data(
            start_date=start_date,
            end_date=end_date,
            data_type='receita',
            is_budget=False,
            limit=100000
        )
        
        if not data:
            return {
                "success": True,
                "data": {
                    "saldo_total": 0,
                    "mom_analysis": [],
                    "meses_disponiveis": [],
                    "pmr": "30 dias"
                }
            }
        
        # Calcular saldo total
        saldo_total = sum(item['value'] for item in data)
        
        # Calcular análise MoM (sempre retorna todos os meses disponíveis)
        mom_data = calcular_mom_postgresql(data, 'receita')
        
        # Calcular meses disponíveis
        meses_disponiveis = sorted(list(set(
            datetime.strptime(str(item['date']), '%Y-%m-%d').strftime('%Y-%m') 
            for item in data
        )))
        
        # Calcular PMR
        pmr_data = calcular_pmr_pmp_postgresql(data, 'receita')
        
        return {
            "success": True,
            "data": {
                "saldo_total": round(saldo_total, 2),
                "mom_analysis": mom_data,
                "meses_disponiveis": meses_disponiveis,
                "pmr": pmr_data.get("pmr")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados de receber: {str(e)}")

@router.get("/pagar")
async def get_pagar_saldo(
    mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM"),
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Endpoint para contas a pagar - compatível com versão Excel"""
    
    try:
        # Definir período baseado no filtro de mês
        if mes:
            # Parse do mês YYYY-MM
            year, month = map(int, mes.split('-'))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            # Todo o período disponível
            start_date = date(2020, 1, 1)  # Data mínima
            end_date = date(2030, 12, 31)  # Data máxima
        
        # Buscar dados de despesa
        data = repository.get_financial_data(
            start_date=start_date,
            end_date=end_date,
            data_type='despesa',
            is_budget=False,
            limit=100000
        )
        
        if not data:
            return {
                "success": True,
                "data": {
                    "saldo_total": 0,
                    "mom_analysis": [],
                    "meses_disponiveis": [],
                    "pmp": "30 dias"
                }
            }
        
        # Calcular saldo total
        saldo_total = sum(item['value'] for item in data)
        
        # Calcular análise MoM (sempre retorna todos os meses disponíveis)
        mom_data = calcular_mom_postgresql(data, 'despesa')
        
        # Calcular meses disponíveis
        meses_disponiveis = sorted(list(set(
            datetime.strptime(str(item['date']), '%Y-%m-%d').strftime('%Y-%m') 
            for item in data
        )))
        
        # Calcular PMP
        pmp_data = calcular_pmr_pmp_postgresql(data, 'despesa')
        
        return {
            "success": True,
            "data": {
                "saldo_total": round(saldo_total, 2),
                "mom_analysis": mom_data,
                "meses_disponiveis": meses_disponiveis,
                "pmp": pmp_data.get("pmp")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados de pagar: {str(e)}")

@router.get("/dfc")
async def get_dfc_postgresql(
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Endpoint DFC para PostgreSQL - usando estruturas migradas do Excel"""
    
    try:
        # Buscar todos os dados financeiros - FILTRAR dados inconsistentes
        data = repository.get_financial_data(
            start_date=date(2020, 1, 1),
            end_date=date(2030, 12, 31),
            limit=100000
        )
        
        # Filtrar dados fictícios e inconsistentes - REMOVENDO DADOS DE EXEMPLO
        if data:
            # Converter para DataFrame para facilitar filtragem
            df_raw = pd.DataFrame(data)
            original_count = len(df_raw)
            
            # 1. REMOVER DADOS FICTÍCIOS específicos (IDs 15354-15533)
            if 'id' in df_raw.columns:
                df_raw = df_raw[~df_raw['id'].between(15354, 15533)]
            
            # 2. REMOVER dados criados em 08/08/2025 (dados fictícios)
            if 'created_at' in df_raw.columns:
                df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
                df_raw = df_raw[~(df_raw['created_at'].dt.date == pd.to_datetime('2025-08-08').date())]
            
            # 3. REMOVER dados com source = "Sistema ERP" (fictícios)
            if 'source' in df_raw.columns:
                df_raw = df_raw[df_raw['source'] != 'Sistema ERP']
            
            # 4. Aplicar filtros de qualidade dos dados
            # Manter apenas dados com categoria válida (não nan, não nula)
            df_raw = df_raw[df_raw['category'].notna()]
            df_raw = df_raw[df_raw['category'] != 'nan']
            df_raw = df_raw[df_raw['category'].str.strip() != '']
            
            # 5. Remover duplicatas exatas
            df_raw = df_raw.drop_duplicates(subset=['category', 'subcategory', 'description', 'value', 'type', 'date'])
            
            # 6. Filtrar por anos válidos (mesmos anos do Excel: 2023-2025)
            df_raw['date'] = pd.to_datetime(df_raw['date'])
            df_raw['ano'] = df_raw['date'].dt.year
            df_raw = df_raw[df_raw['ano'].isin([2023, 2024, 2025])]
            
            # Converter de volta para lista de dicts
            data = df_raw.to_dict('records')
            
            print(f"🧹 Dados filtrados (removidos fictícios): {original_count} → {len(data)} registros")
            print(f"🎯 Meta Excel: 15338 registros")
            print(f"📊 Diferença: {len(data) - 15338} registros")
        
        print(f"🔍 DFC PostgreSQL - Iniciando processamento")
        print(f"📊 Total de registros financeiros: {len(data)}")
        
        if not data:
            return {
                "success": True,
                "meses": [],
                "trimestres": [],
                "anos": [],
                "data": []
            }
        
        # Processar dados para DFC
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['mes'] = df['date'].dt.strftime('%Y-%m')
        df['ano'] = df['date'].dt.year
        df['trimestre'] = df['date'].dt.to_period('Q').astype(str)
        
        # 🔧 SEPARAR OPERADORES DOS NOMES DAS CATEGORIAS
        # Extrair operador e nome limpo das categorias que vieram do Excel
        def extrair_operador_e_nome(categoria):
            """Extrai operador e nome limpo da categoria do Excel"""
            if pd.isna(categoria) or categoria == 'nan':
                return None, None
            
            categoria_str = str(categoria).strip()
            
            # Padrão: ( OPERADOR ) NOME
            import re
            match = re.match(r'\(\s*([=+\-+/\*])\s*\)\s*(.*)', categoria_str)
            if match:
                operador = match.group(1)
                nome_limpo = match.group(2).strip()
                return operador, nome_limpo
            else:
                # Se não tem operador, é um nome direto
                return None, categoria_str
        
        # Aplicar separação nas categorias
        df[['operador_categoria', 'nome_categoria']] = df['category'].apply(
            lambda x: pd.Series(extrair_operador_e_nome(x))
        )
        
        # Usar nome_categoria para os matches, mantendo o operador para cálculos
        df['category_clean'] = df['nome_categoria']
        
        # Períodos únicos
        meses = sorted(df['mes'].unique())
        print(f"📅 Períodos encontrados: {meses[:5]}... (total: {len(meses)})")
        
        # Debug: mostrar categorias disponíveis
        categorias_unicas = df['category'].unique()
        print(f"🏷️ Categorias nos dados: {categorias_unicas[:10]}... (total: {len(categorias_unicas)})")
        print(f"🏷️ Categorias limpas: {df['category_clean'].unique()[:10]}... (total: {len(df['category_clean'].unique())})")
        print(f"💰 Valores únicos: {df['value'].unique()[:10]}... (total: {len(df['value'].unique())})")
        print(f"📅 Períodos: {meses[:5]}... (total: {len(meses)})")
        anos = sorted(df['ano'].unique())
        trimestres = sorted(df['trimestre'].unique())
        
        # Buscar estruturas DFC do banco
        from database.schema_sqlalchemy import DFCStructureN1, DFCStructureN2, DFCClassification
        from sqlalchemy.orm import sessionmaker
        from database.connection_sqlalchemy import get_engine
        
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Buscar estruturas DFC
            dfc_n1_items = session.query(DFCStructureN1).order_by(DFCStructureN1.order_index).all()
            dfc_n2_items = session.query(DFCStructureN2).order_by(DFCStructureN2.order_index).all()
            
            print(f"🏗️ Estruturas DFC N1: {len(dfc_n1_items)}")
            print(f"🏗️ Estruturas DFC N2: {len(dfc_n2_items)}")
            
            if not dfc_n1_items:
                # Se não houver estruturas migradas, usar estrutura básica
                return await get_dfc_basic_structure(df, meses, trimestres, anos)
            
            # Criar estrutura DFC baseada nas estruturas migradas
            result = []
            
            # 1. Saldo Inicial
            saldo_inicial = {
                "nome": "Saldo inicial",
                "tipo": "=",
                "valor": 0.0,
                "valores_mensais": {mes: 0.0 for mes in meses},
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "horizontal_mensais": {mes: "–" for mes in meses},
                "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                "horizontal_anuais": {str(ano): "–" for ano in anos}
            }
            result.append(saldo_inicial)
            
            # 2. Movimentações por estrutura DFC
            movimentacoes = {
                "nome": "Movimentações",
                "tipo": "=",
                "valor": 0.0,
                "valores_mensais": {mes: 0.0 for mes in meses},
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "horizontal_mensais": {mes: "–" for mes in meses},
                "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                "horizontal_anuais": {str(ano): "–" for ano in anos},
                "classificacoes": []
            }
            
            # Processar cada item DFC N1 (totalizador)
            for dfc_n1_item in dfc_n1_items:
                print(f"  📊 Processando totalizador: {dfc_n1_item.name}")
                
                totalizador = {
                    "nome": dfc_n1_item.name,
                    "tipo": dfc_n1_item.operation_type,
                    "valor": 0.0,
                    "valores_mensais": {mes: 0.0 for mes in meses},
                    "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                    "valores_anuais": {str(ano): 0.0 for ano in anos},
                    "orcamentos_mensais": {mes: 0.0 for mes in meses},
                    "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                    "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                    "horizontal_mensais": {mes: "–" for mes in meses},
                    "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                    "horizontal_anuais": {str(ano): "–" for ano in anos},
                    "classificacoes": []
                }
                
                # Buscar contas DFC N2 deste totalizador
                contas_n2 = [item for item in dfc_n2_items if item.dfc_n1_id == dfc_n1_item.dfc_n1_id]
                print(f"    📋 Contas N2 encontradas: {len(contas_n2)}")
                
                # Adicionar contas DFC N2 como classificações do totalizador
                for conta_n2 in contas_n2:
                    print(f"      💰 Processando conta N2: {conta_n2.name}")
                    
                    # Buscar classificações desta conta DFC N2
                    classificacoes_conta = session.query(DFCClassification).filter(
                        DFCClassification.dfc_n2_id == conta_n2.dfc_n2_id
                    ).all()
                    
                    print(f"        🏷️ Classificações encontradas: {len(classificacoes_conta)}")
                    
                    # Buscar dados financeiros que correspondem às classificações desta conta
                    df_conta = pd.DataFrame()
                    matches_encontrados = 0
                    for classificacao in classificacoes_conta:
                        # Tentar match exato primeiro com nome limpo
                        df_match = df[df['category_clean'] == classificacao.name]
                        if df_match.empty:
                            # Tentar match parcial - classificação contém categoria limpa
                            mask = df['category_clean'].apply(lambda x: str(x).lower() in str(classificacao.name).lower() if pd.notna(x) and x.strip() else False)
                            df_match = df[mask]
                        if df_match.empty:
                            # Tentar match reverso - categoria limpa contém classificação
                            palavras_classificacao = str(classificacao.name).lower().split()
                            for palavra in palavras_classificacao:
                                if len(palavra) > 3:  # Ignorar palavras muito pequenas como "e", "de", etc.
                                    mask = df['category_clean'].apply(lambda x: palavra in str(x).lower() if pd.notna(x) else False)
                                    df_temp = df[mask]
                                    df_match = pd.concat([df_match, df_temp], ignore_index=True)
                        
                        if not df_match.empty:
                            matches_encontrados += len(df_match)
                        df_conta = pd.concat([df_conta, df_match], ignore_index=True)
                    
                    print(f"          🔍 Matches encontrados: {matches_encontrados} registros")
                    
                    # Remover duplicatas se houver
                    df_conta = df_conta.drop_duplicates()
                    
                    if not df_conta.empty:
                        # Calcular valores por período
                        for mes in meses:
                            df_mes = df_conta[df_conta['mes'] == mes]
                            receitas = float(df_mes[df_mes['type'] == 'receita']['value'].sum())
                            despesas = float(df_mes[df_mes['type'] == 'despesa']['value'].sum())
                            valor_mes = receitas - despesas
                            
                            # Aplicar tipo de operação
                            if conta_n2.operation_type == '+':
                                valor_mes = abs(valor_mes)
                            elif conta_n2.operation_type == '-':
                                valor_mes = -abs(valor_mes)
                            
                            totalizador["valores_mensais"][mes] += valor_mes
                            movimentacoes["valores_mensais"][mes] += valor_mes
                        
                        for tri in trimestres:
                            df_tri = df_conta[df_conta['trimestre'] == tri]
                            receitas = float(df_tri[df_tri['type'] == 'receita']['value'].sum())
                            despesas = float(df_tri[df_tri['type'] == 'despesa']['value'].sum())
                            valor_tri = receitas - despesas
                            
                            if conta_n2.operation_type == '+':
                                valor_tri = abs(valor_tri)
                            elif conta_n2.operation_type == '-':
                                valor_tri = -abs(valor_tri)
                            
                            totalizador["valores_trimestrais"][tri] += valor_tri
                            movimentacoes["valores_trimestrais"][tri] += valor_tri
                        
                        for ano in anos:
                            df_ano = df_conta[df_conta['ano'] == ano]
                            receitas = float(df_ano[df_ano['type'] == 'receita']['value'].sum())
                            despesas = float(df_ano[df_ano['type'] == 'despesa']['value'].sum())
                            valor_ano = receitas - despesas
                            
                            if conta_n2.operation_type == '+':
                                valor_ano = abs(valor_ano)
                            elif conta_n2.operation_type == '-':
                                valor_ano = -abs(valor_ano)
                            
                            totalizador["valores_anuais"][str(ano)] += valor_ano
                            movimentacoes["valores_anuais"][str(ano)] += valor_ano
                        
                        # Criar item para a conta DFC N2
                        conta_n2_item = {
                            "nome": conta_n2.name,
                            "tipo": conta_n2.operation_type,
                            "valor": 0.0,
                            "valores_mensais": {mes: 0.0 for mes in meses},
                            "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                            "valores_anuais": {str(ano): 0.0 for ano in anos},
                            "orcamentos_mensais": {mes: 0.0 for mes in meses},
                            "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                            "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                            "horizontal_mensais": {mes: "–" for mes in meses},
                            "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                            "horizontal_anuais": {str(ano): "–" for ano in anos},
                            "classificacoes": []
                        }
                        
                        # Calcular valores por período para a conta DFC N2
                        for mes in meses:
                            df_mes = df_conta[df_conta['mes'] == mes]
                            receitas = float(df_mes[df_mes['type'] == 'receita']['value'].sum())
                            despesas = float(df_mes[df_mes['type'] == 'despesa']['value'].sum())
                            valor_mes = receitas - despesas
                            
                            if conta_n2.operation_type == '+':
                                valor_mes = abs(valor_mes)
                            elif conta_n2.operation_type == '-':
                                valor_mes = -abs(valor_mes)
                            
                            conta_n2_item["valores_mensais"][mes] = valor_mes
                        
                        for tri in trimestres:
                            df_tri = df_conta[df_conta['trimestre'] == tri]
                            receitas = float(df_tri[df_tri['type'] == 'receita']['value'].sum())
                            despesas = float(df_tri[df_tri['type'] == 'despesa']['value'].sum())
                            valor_tri = receitas - despesas
                            
                            if conta_n2.operation_type == '+':
                                valor_tri = abs(valor_tri)
                            elif conta_n2.operation_type == '-':
                                valor_tri = -abs(valor_tri)
                            
                            conta_n2_item["valores_trimestrais"][tri] = valor_tri
                        
                        for ano in anos:
                            df_ano = df_conta[df_conta['ano'] == ano]
                            receitas = float(df_ano[df_ano['type'] == 'receita']['value'].sum())
                            despesas = float(df_ano[df_ano['type'] == 'despesa']['value'].sum())
                            valor_ano = receitas - despesas
                            
                            if conta_n2.operation_type == '+':
                                valor_ano = abs(valor_ano)
                            elif conta_n2.operation_type == '-':
                                valor_ano = -abs(valor_ano)
                            
                            conta_n2_item["valores_anuais"][str(ano)] = valor_ano
                        
                        # Calcular valor total da conta DFC N2
                        conta_n2_item["valor"] = float(sum(conta_n2_item["valores_mensais"].values()))
                        
                        # Adicionar classificações DFC como itens da conta N2
                        for classificacao in classificacoes_conta:
                            # Buscar dados desta classificação específica
                            df_class = pd.DataFrame()
                            # Tentar match exato primeiro
                            df_match = df_conta[df_conta['category'] == classificacao.name]
                            if df_match.empty:
                                # Tentar match parcial
                                df_match = df_conta[df_conta['category'].str.contains(classificacao.name, case=False, na=False, regex=False)]
                            if df_match.empty:
                                # Tentar match reverso
                                mask = df_conta['category'].apply(lambda x: str(classificacao.name).lower() in str(x).lower() if pd.notna(x) else False)
                                df_match = df_conta[mask]
                            df_class = df_match
                            
                            if not df_class.empty:
                                receitas_class = float(df_class[df_class['type'] == 'receita']['value'].sum())
                                despesas_class = float(df_class[df_class['type'] == 'despesa']['value'].sum())
                                valor_class = receitas_class - despesas_class
                                
                                if conta_n2.operation_type == '+':
                                    valor_class = abs(valor_class)
                                elif conta_n2.operation_type == '-':
                                    valor_class = -abs(valor_class)
                                
                                classificacao_item = {
                                    "nome": classificacao.name,
                                    "valor": valor_class,
                                    "valores_mensais": {},
                                    "valores_trimestrais": {},
                                    "valores_anuais": {},
                                    "horizontal_mensais": {mes: "–" for mes in meses},
                                    "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                                    "horizontal_anuais": {str(ano): "–" for ano in anos}
                                }
                                
                                # Calcular valores por período para classificação
                                for mes in meses:
                                    df_class_mes = df_class[df_class['mes'] == mes]
                                    receitas_mes = float(df_class_mes[df_class_mes['type'] == 'receita']['value'].sum())
                                    despesas_mes = float(df_class_mes[df_class_mes['type'] == 'despesa']['value'].sum())
                                    valor_mes = receitas_mes - despesas_mes
                                    
                                    if conta_n2.operation_type == '+':
                                        valor_mes = abs(valor_mes)
                                    elif conta_n2.operation_type == '-':
                                        valor_mes = -abs(valor_mes)
                                    
                                    classificacao_item["valores_mensais"][mes] = valor_mes
                                
                                for tri in trimestres:
                                    df_class_tri = df_class[df_class['trimestre'] == tri]
                                    receitas_tri = float(df_class_tri[df_class_tri['type'] == 'receita']['value'].sum())
                                    despesas_tri = float(df_class_tri[df_class_tri['type'] == 'despesa']['value'].sum())
                                    valor_tri = receitas_tri - despesas_tri
                                    
                                    if conta_n2.operation_type == '+':
                                        valor_tri = abs(valor_tri)
                                    elif conta_n2.operation_type == '-':
                                        valor_tri = -abs(valor_tri)
                                    
                                    classificacao_item["valores_trimestrais"][tri] = valor_tri
                                
                                for ano in anos:
                                    df_class_ano = df_class[df_class['ano'] == ano]
                                    receitas_ano = float(df_class_ano[df_class_ano['type'] == 'receita']['value'].sum())
                                    despesas_ano = float(df_class_ano[df_class_ano['type'] == 'despesa']['value'].sum())
                                    valor_ano = receitas_ano - despesas_ano
                                    
                                    if conta_n2.operation_type == '+':
                                        valor_ano = abs(valor_ano)
                                    elif conta_n2.operation_type == '-':
                                        valor_ano = -abs(valor_ano)
                                    
                                    classificacao_item["valores_anuais"][str(ano)] = valor_ano
                                
                                conta_n2_item["classificacoes"].append(classificacao_item)
                        
                        # Adicionar conta DFC N2 como classificação do totalizador
                        totalizador["classificacoes"].append(conta_n2_item)
                
                # Calcular valor total do totalizador
                totalizador["valor"] = float(sum(totalizador["valores_mensais"].values()))
                
                # Adicionar totalizador às movimentações
                movimentacoes["classificacoes"].append(totalizador)
            
            # Calcular valor total das movimentações
            movimentacoes["valor"] = float(sum(movimentacoes["valores_mensais"].values()))
            
            result.append(movimentacoes)
            
            # 3. Saldo Final
            saldo_final = {
                "nome": "Saldo final",
                "tipo": "=",
                "valor": float(movimentacoes["valor"]),
                "valores_mensais": {mes: 0.0 for mes in meses},
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "orcamento_total": 0.0,
                "horizontal_mensais": {mes: "–" for mes in meses},
                "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                "horizontal_anuais": {str(ano): "–" for ano in anos}
            }
            
            # Calcular saldo final por período
            for mes in meses:
                saldo_final["valores_mensais"][mes] = float(movimentacoes["valores_mensais"][mes])
            
            for tri in trimestres:
                saldo_final["valores_trimestrais"][tri] = float(movimentacoes["valores_trimestrais"][tri])
            
            for ano in anos:
                saldo_final["valores_anuais"][str(ano)] = float(movimentacoes["valores_anuais"][str(ano)])
            
            result.append(saldo_final)
            
            # Preparar dados de orçamento por período (como nos endpoints Excel)
            orcamentos_mensais = {}
            orcamentos_trimestrais = {}
            orcamentos_anuais = {}
            orcamentos_totais = {}
            
            for mes in meses:
                orcamentos_mensais[mes] = {}
                for item in result:
                    orcamentos_mensais[mes][item["nome"]] = item["orcamentos_mensais"].get(mes, 0.0)
            
            for tri in trimestres:
                orcamentos_trimestrais[tri] = {}
                for item in result:
                    orcamentos_trimestrais[tri][item["nome"]] = item["orcamentos_trimestrais"].get(tri, 0.0)
            
            for ano in anos:
                orcamentos_anuais[str(ano)] = {}
                for item in result:
                    orcamentos_anuais[str(ano)][item["nome"]] = item["orcamentos_anuais"].get(str(ano), 0.0)
            
            for item in result:
                orcamentos_totais[item["nome"]] = item["orcamento_total"]
            
            return {
                "success": True,
                "meses": [str(mes) for mes in meses],
                "trimestres": [str(tri) for tri in trimestres],
                "anos": [str(ano) for ano in anos],
                "data": result,
                "orcamentos_mensais": orcamentos_mensais,
                "orcamentos_trimestrais": orcamentos_trimestrais,
                "orcamentos_anuais": orcamentos_anuais,
                "orcamento_total": orcamentos_totais
            }
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Erro no DFC: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DFC: {str(e)}")

async def get_dfc_basic_structure(df, meses, trimestres, anos):
    """Estrutura DFC básica quando não há estruturas migradas"""
    # Processar dados para DFC
    # df já é um DataFrame, não precisa converter
    df['date'] = pd.to_datetime(df['date'])
    df['mes'] = df['date'].dt.strftime('%Y-%m')
    df['ano'] = df['date'].dt.year
    df['trimestre'] = df['date'].dt.to_period('Q').astype(str)
    
    # Períodos únicos
    meses = sorted(df['mes'].unique())
    anos = sorted(df['ano'].unique())
    trimestres = sorted(df['trimestre'].unique())
    
    # Criar estrutura DFC básica
    result = []
    
    # 1. Saldo Inicial
    saldo_inicial = {
        "nome": "Saldo inicial",
        "tipo": "=",
        "valor": 0.0,
        "valores_mensais": {mes: 0.0 for mes in meses},
        "valores_trimestrais": {tri: 0.0 for tri in trimestres},
        "valores_anuais": {str(ano): 0.0 for ano in anos},
        "orcamentos_mensais": {mes: 0.0 for mes in meses},
        "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
        "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
        "orcamento_total": 0.0,
        "horizontal_mensais": {mes: "–" for mes in meses},
        "horizontal_trimestrais": {tri: "–" for tri in trimestres},
        "horizontal_anuais": {str(ano): "–" for ano in anos}
    }
    result.append(saldo_inicial)
    
    # 2. Movimentações
    movimentacoes = {
        "nome": "Movimentações",
        "tipo": "=",
        "valor": 0.0,
        "valores_mensais": {mes: 0.0 for mes in meses},
        "valores_trimestrais": {tri: 0.0 for tri in trimestres},
        "valores_anuais": {str(ano): 0.0 for ano in anos},
        "orcamentos_mensais": {mes: 0.0 for mes in meses},
        "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
        "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
        "orcamento_total": 0.0,
        "horizontal_mensais": {mes: "–" for mes in meses},
        "horizontal_trimestrais": {tri: "–" for tri in trimestres},
        "horizontal_anuais": {str(ano): "–" for ano in anos},
        "classificacoes": []
    }
    
    # Calcular movimentações por mês
    for mes in meses:
        df_mes = df[df['mes'] == mes]
        receitas = float(df_mes[df_mes['type'] == 'receita']['value'].sum())
        despesas = float(df_mes[df_mes['type'] == 'despesa']['value'].sum())
        movimentacoes["valores_mensais"][mes] = receitas - despesas
        movimentacoes["orcamentos_mensais"][mes] = 0.0  # Sem dados orçamentários
        movimentacoes["horizontal_mensais"][mes] = "–"
    
    # Calcular movimentações por trimestre
    for tri in trimestres:
        df_tri = df[df['trimestre'] == tri]
        receitas = float(df_tri[df_tri['type'] == 'receita']['value'].sum())
        despesas = float(df_tri[df_tri['type'] == 'despesa']['value'].sum())
        movimentacoes["valores_trimestrais"][tri] = receitas - despesas
        movimentacoes["orcamentos_trimestrais"][tri] = 0.0  # Sem dados orçamentários
        movimentacoes["horizontal_trimestrais"][tri] = "–"
    
    # Calcular movimentações por ano
    for ano in anos:
        df_ano = df[df['ano'] == ano]
        receitas = float(df_ano[df_ano['type'] == 'receita']['value'].sum())
        despesas = float(df_ano[df_ano['type'] == 'despesa']['value'].sum())
        movimentacoes["valores_anuais"][str(ano)] = receitas - despesas
        movimentacoes["orcamentos_anuais"][str(ano)] = 0.0  # Sem dados orçamentários
        movimentacoes["horizontal_anuais"][str(ano)] = "–"
    
    # Valor total das movimentações
    movimentacoes["valor"] = float(sum(movimentacoes["valores_mensais"].values()))
    
    # Adicionar classificações por categoria (simplificado)
    categorias = df['category'].unique()
    for categoria in categorias:
        df_cat = df[df['category'] == categoria]
        receitas_cat = float(df_cat[df_cat['type'] == 'receita']['value'].sum())
        despesas_cat = float(df_cat[df_cat['type'] == 'despesa']['value'].sum())
        
        if receitas_cat > 0 or despesas_cat > 0:
            classificacao = {
                "nome": str(categoria),
                "valor": receitas_cat - despesas_cat,
                "valores_mensais": {mes: 0.0 for mes in meses},
                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                "valores_anuais": {str(ano): 0.0 for ano in anos},
                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                "orcamento_total": 0.0,
                "horizontal_mensais": {mes: "–" for mes in meses},
                "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                "horizontal_anuais": {str(ano): "–" for ano in anos}
            }
            
            # Calcular valores por período para esta categoria
            for mes in meses:
                df_cat_mes = df_cat[df_cat['mes'] == mes]
                receitas_mes = float(df_cat_mes[df_cat_mes['type'] == 'receita']['value'].sum())
                despesas_mes = float(df_cat_mes[df_cat_mes['type'] == 'despesa']['value'].sum())
                classificacao["valores_mensais"][mes] = receitas_mes - despesas_mes
            
            for tri in trimestres:
                df_cat_tri = df_cat[df_cat['trimestre'] == tri]
                receitas_tri = float(df_cat_tri[df_cat_tri['type'] == 'receita']['value'].sum())
                despesas_tri = float(df_cat_tri[df_cat_tri['type'] == 'despesa']['value'].sum())
                classificacao["valores_trimestrais"][tri] = receitas_tri - despesas_tri
            
            for ano in anos:
                df_cat_ano = df_cat[df_cat['ano'] == ano]
                receitas_ano = float(df_cat_ano[df_cat_ano['type'] == 'receita']['value'].sum())
                despesas_ano = float(df_cat_ano[df_cat_ano['type'] == 'despesa']['value'].sum())
                classificacao["valores_anuais"][str(ano)] = receitas_ano - despesas_ano
            
            movimentacoes["classificacoes"].append(classificacao)
    
    result.append(movimentacoes)
    
    # 3. Saldo Final
    saldo_final = {
        "nome": "Saldo final",
        "tipo": "=",
        "valor": float(movimentacoes["valor"]),
        "valores_mensais": {},
        "valores_trimestrais": {},
        "valores_anuais": {},
        "horizontal_mensais": {mes: "–" for mes in meses},
        "horizontal_trimestrais": {tri: "–" for tri in trimestres},
        "horizontal_anuais": {str(ano): "–" for ano in anos}
    }
    
    # Calcular saldo final por período (saldo inicial + movimentações)
    for mes in meses:
        saldo_final["valores_mensais"][mes] = float(movimentacoes["valores_mensais"][mes])
    
    for tri in trimestres:
        saldo_final["valores_trimestrais"][tri] = float(movimentacoes["valores_trimestrais"][tri])
    
    for ano in anos:
        saldo_final["valores_anuais"][str(ano)] = float(movimentacoes["valores_anuais"][str(ano)])
    
    result.append(saldo_final)
    
    return {
        "success": True,
        "meses": [str(mes) for mes in meses],
        "trimestres": [str(tri) for tri in trimestres],
        "anos": [str(ano) for ano in anos],
        "data": result
    }

@router.get("/dre")
async def get_dre_postgresql(
    repository: FinancialDataRepository = Depends(get_financial_repository)
):
    """Endpoint DRE para PostgreSQL - usando estruturas migradas do Excel"""
    
    try:
        # Buscar todos os dados financeiros - FILTRAR dados inconsistentes
        data = repository.get_financial_data(
            start_date=date(2020, 1, 1),
            end_date=date(2030, 12, 31),
            limit=100000
        )
        
        # Filtrar dados fictícios e inconsistentes - REMOVENDO DADOS DE EXEMPLO
        if data:
            # Converter para DataFrame para facilitar filtragem
            df_raw = pd.DataFrame(data)
            original_count = len(df_raw)
            
            # 1. REMOVER DADOS FICTÍCIOS específicos (IDs 15354-15533)
            if 'id' in df_raw.columns:
                df_raw = df_raw[~df_raw['id'].between(15354, 15533)]
            
            # 2. REMOVER dados criados em 08/08/2025 (dados fictícios)
            if 'created_at' in df_raw.columns:
                df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
                df_raw = df_raw[~(df_raw['created_at'].dt.date == pd.to_datetime('2025-08-08').date())]
            
            # 3. REMOVER dados com source = "Sistema ERP" (fictícios)
            if 'source' in df_raw.columns:
                df_raw = df_raw[df_raw['source'] != 'Sistema ERP']
            
            # 4. Aplicar filtros de qualidade dos dados
            # Manter apenas dados com categoria válida (não nan, não nula)
            df_raw = df_raw[df_raw['category'].notna()]
            df_raw = df_raw[df_raw['category'] != 'nan']
            df_raw = df_raw[df_raw['category'].str.strip() != '']
            
            # 5. Remover duplicatas exatas
            df_raw = df_raw.drop_duplicates(subset=['category', 'subcategory', 'description', 'value', 'type', 'date'])
            
            # 6. Filtrar por anos válidos (mesmos anos do Excel: 2023-2025)
            df_raw['date'] = pd.to_datetime(df_raw['date'])
            df_raw['ano'] = df_raw['date'].dt.year
            df_raw = df_raw[df_raw['ano'].isin([2023, 2024, 2025])]
            
            # Converter de volta para lista de dicts
            data = df_raw.to_dict('records')
            
            print(f"🧹 Dados filtrados (removidos fictícios): {original_count} → {len(data)} registros")
            print(f"🎯 Meta Excel: 15338 registros")
            print(f"📊 Diferença: {len(data) - 15338} registros")
        
        print(f"🔍 DRE PostgreSQL - Iniciando processamento")
        print(f"📊 Total de registros financeiros: {len(data)}")
        
        if not data:
            return {
                "success": True,
                "meses": [],
                "trimestres": [],
                "anos": [],
                "data": []
            }
        
        # Processar dados para DRE usando a mesma lógica da versão Excel
        df = pd.DataFrame(data)
        
        # Usar as colunas corretas da tabela financial_data (como na versão Excel)
        df['competencia'] = pd.to_datetime(df['competencia'], errors="coerce")
        df['mes_ano'] = df['competencia'].dt.to_period("M").astype(str)
        df['ano'] = df['competencia'].dt.year
        df['trimestre'] = df['competencia'].dt.to_period("Q").apply(lambda p: f"{p.year}-T{p.quarter}")
        
        # Converter valor para numérico (usar valor_original como na versão Excel)
        df['valor_original'] = pd.to_numeric(df['valor_original'], errors="coerce")
        df = df.dropna(subset=['competencia', 'valor_original'])
        
        # Períodos únicos
        meses = sorted(df['mes_ano'].dropna().unique())
        anos = sorted(set(int(a) for a in df['ano'].dropna().unique()))
        trimestres = sorted(df['trimestre'].dropna().unique())
        
        # Separar realizado e orçamento baseado na coluna 'origem' (como na versão Excel)
        df_real = df[df['origem'] != "ORC"].copy()
        df_orc = df[df['origem'] == "ORC"].copy()
        
        # Usar dre_n2 diretamente (como na versão Excel)
        df_real['category_clean'] = df_real['dre_n2']
        df_orc['category_clean'] = df_orc['dre_n2']
        
        if df_orc.empty:
            # Criar DataFrame vazio com a mesma estrutura (como na versão Excel)
            df_orc = df_real.copy()
            df_orc['valor_original'] = 0.0
            df_orc['origem'] = 'ORC'
        
        print(f"📅 Períodos encontrados: {meses[:5]}... (total: {len(meses)})")
        
        # Debug: mostrar categorias disponíveis
        categorias_unicas = df['dre_n2'].unique()
        print(f"🏷️ Categorias DRE N2: {categorias_unicas[:10]}... (total: {len(categorias_unicas)})")
        print(f"💰 Valores únicos: {df['valor_original'].unique()[:10]}... (total: {len(df['valor_original'].unique())})")
        print(f"📅 Períodos: {meses[:5]}... (total: {len(meses)})")
        
        # Buscar estruturas DRE do banco
        from database.schema_sqlalchemy import DREStructureN1, DREStructureN2, DREClassification
        from sqlalchemy.orm import sessionmaker
        from database.connection_sqlalchemy import get_engine
        
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Buscar estruturas DRE
            dre_n1_items = session.query(DREStructureN1).order_by(DREStructureN1.order_index).all()
            dre_n2_items = session.query(DREStructureN2).order_by(DREStructureN2.order_index).all()
            
            print(f"🏗️ Estruturas DRE N1: {len(dre_n1_items)}")
            print(f"🏗️ Estruturas DRE N2: {len(dre_n2_items)}")
            
            if not dre_n1_items:
                # Se não houver estruturas migradas, usar estrutura básica
                return await get_dre_basic_structure(df, meses, trimestres, anos)
            
            # Criar estrutura DRE baseada nas estruturas migradas
            result = []
            
            # Processar cada totalizador DRE N1
            for totalizador_n1 in dre_n1_items:
                totalizador_item = {
                    "nome": totalizador_n1.name,
                    "tipo": totalizador_n1.operation_type,
                    "valor": 0.0,
                    "valores_mensais": {mes: 0.0 for mes in meses},
                    "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                    "valores_anuais": {str(ano): 0.0 for ano in anos},
                    "orcamentos_mensais": {mes: 0.0 for mes in meses},
                    "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                    "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                    "horizontal_mensais": {mes: "–" for mes in meses},
                    "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                    "horizontal_anuais": {str(ano): "–" for ano in anos},
                    "vertical_mensais": {mes: "–" for mes in meses},
                    "vertical_trimestrais": {tri: "–" for tri in trimestres},
                    "vertical_anuais": {str(ano): "–" for ano in anos},
                    "classificacoes": []
                }
                
                # Buscar contas DRE N2 filhas deste totalizador
                contas_n2 = [item for item in dre_n2_items if item.dre_n1_id == totalizador_n1.dre_n1_id]
                
                for conta_n2 in contas_n2:
                    conta_n2_item = {
                        "nome": conta_n2.name,
                        "tipo": conta_n2.operation_type,
                        "valor": 0.0,
                        "valores_mensais": {mes: 0.0 for mes in meses},
                        "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                        "valores_anuais": {str(ano): 0.0 for ano in anos},
                        "orcamentos_mensais": {mes: 0.0 for mes in meses},
                        "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                        "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                        "horizontal_mensais": {mes: "–" for mes in meses},
                        "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                        "horizontal_anuais": {str(ano): "–" for ano in anos},
                        "vertical_mensais": {mes: "–" for mes in meses},
                        "vertical_trimestrais": {tri: "–" for tri in trimestres},
                        "vertical_anuais": {str(ano): "–" for ano in anos},
                        "classificacoes": []
                    }
                    
                    # Buscar dados financeiros para esta conta DRE N2
                    print(f"      🔍 Buscando dados para conta: '{conta_n2.name}'")
                    print(f"      📊 Categorias disponíveis: {df_real['category_clean'].unique()[:10]}")
                    
                    # Match exato primeiro
                    df_conta_real = df_real[df_real['category_clean'] == conta_n2.name]
                    df_conta_orc = df_orc[df_orc['category_clean'] == conta_n2.name]
                    
                    # Se não encontrou, tentar match parcial
                    if df_conta_real.empty:
                        print(f"      ⚠️ Match exato não encontrado, tentando parcial...")
                        mask_real = df_real['category_clean'].apply(
                            lambda x: str(x).lower() in str(conta_n2.name).lower() if pd.notna(x) else False
                        )
                        df_conta_real = df_real[mask_real]
                        
                        mask_orc = df_orc['category_clean'].apply(
                            lambda x: str(x).lower() in str(conta_n2.name).lower() if pd.notna(x) else False
                        )
                        df_conta_orc = df_orc[mask_orc]
                    
                    print(f"      ✅ Dados encontrados - Realizado: {len(df_conta_real)}, Orçamento: {len(df_conta_orc)}")
                    
                    if not df_conta_real.empty:
                        # Calcular valores por período para a conta (REALIZADO)
                        for mes in meses:
                            df_mes_real = df_conta_real[df_conta_real['mes'] == mes]
                            df_mes_orc = df_conta_orc[df_conta_orc['mes'] == mes]
                            
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
                        
                        # Trimestres
                        for tri in trimestres:
                            df_tri_real = df_conta_real[df_conta_real['trimestre'] == tri]
                            df_tri_orc = df_conta_orc[df_conta_orc['trimestre'] == tri]
                            
                            # Realizado
                            receitas_tri_real = float(df_tri_real[df_tri_real['type'] == 'receita']['value'].sum())
                            despesas_tri_real = float(df_tri_real[df_tri_real['type'] == 'despesa']['value'].sum())
                            valor_tri_real = receitas_tri_real - despesas_tri_real
                            
                            # Orçamento
                            receitas_tri_orc = float(df_tri_orc[df_tri_orc['type'] == 'receita']['value'].sum())
                            despesas_tri_orc = float(df_tri_orc[df_tri_orc['type'] == 'despesa']['value'].sum())
                            valor_tri_orc = receitas_tri_orc - despesas_tri_orc
                            
                            # Aplicar operador matemático
                            if conta_n2.operation_type == '+':
                                valor_tri_real = abs(valor_tri_real)
                                valor_tri_orc = abs(valor_tri_orc)
                            elif conta_n2.operation_type == '-':
                                valor_tri_real = -abs(valor_tri_real)
                                valor_tri_orc = -abs(valor_tri_orc)
                            
                            conta_n2_item["valores_trimestrais"][tri] = valor_tri_real
                            conta_n2_item["orcamentos_trimestrais"][tri] = valor_tri_orc
                            totalizador_item["valores_trimestrais"][tri] += valor_tri_real
                            totalizador_item["orcamentos_trimestrais"][tri] += valor_tri_orc
                        
                        # Anos
                        for ano in anos:
                            df_ano_real = df_conta_real[df_conta_real['ano'] == ano]
                            df_ano_orc = df_conta_orc[df_conta_orc['ano'] == ano]
                            
                            # Realizado
                            receitas_ano_real = float(df_ano_real[df_ano_real['type'] == 'receita']['value'].sum())
                            despesas_ano_real = float(df_ano_real[df_ano_real['type'] == 'despesa']['value'].sum())
                            valor_ano_real = receitas_ano_real - despesas_ano_real
                            
                            # Orçamento
                            receitas_ano_orc = float(df_ano_orc[df_ano_orc['type'] == 'receita']['value'].sum())
                            despesas_ano_orc = float(df_ano_orc[df_ano_orc['type'] == 'despesa']['value'].sum())
                            valor_ano_orc = receitas_ano_orc - despesas_ano_orc
                            
                            # Aplicar operador matemático
                            if conta_n2.operation_type == '+':
                                valor_ano_real = abs(valor_ano_real)
                                valor_ano_orc = abs(valor_ano_orc)
                            elif conta_n2.operation_type == '-':
                                valor_ano_real = -abs(valor_ano_real)
                                valor_ano_orc = -abs(valor_ano_orc)
                            
                            conta_n2_item["valores_anuais"][str(ano)] = valor_ano_real
                            conta_n2_item["orcamentos_anuais"][str(ano)] = valor_ano_orc
                            totalizador_item["valores_anuais"][str(ano)] += valor_ano_real
                            totalizador_item["orcamentos_anuais"][str(ano)] += valor_ano_orc
                        
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
                                "valores_mensais": {mes: 0.0 for mes in meses},
                                "valores_trimestrais": {tri: 0.0 for tri in trimestres},
                                "valores_anuais": {str(ano): 0.0 for ano in anos},
                                "orcamentos_mensais": {mes: 0.0 for mes in meses},
                                "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
                                "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
                                "horizontal_mensais": {mes: "–" for mes in meses},
                                "horizontal_trimestrais": {tri: "–" for tri in trimestres},
                                "horizontal_anuais": {str(ano): "–" for ano in anos}
                            }
                            
                            # Calcular valores por período para classificação (REALIZADO E ORÇAMENTO)
                            for mes in meses:
                                df_class_mes_real = df_conta_real[df_conta_real['mes'] == mes]
                                df_class_mes_orc = df_conta_orc[df_conta_orc['mes'] == mes]
                                
                                # Realizado
                                receitas_mes_real = float(df_class_mes_real[df_class_mes_real['type'] == 'receita']['value'].sum())
                                despesas_mes_real = float(df_class_mes_real[df_class_mes_real['type'] == 'despesa']['value'].sum())
                                valor_mes_real = receitas_mes_real - despesas_mes_real
                                
                                # Orçamento
                                receitas_mes_orc = float(df_class_mes_orc[df_class_mes_orc['type'] == 'receita']['value'].sum())
                                despesas_mes_orc = float(df_class_mes_orc[df_class_mes_orc['type'] == 'despesa']['value'].sum())
                                valor_mes_orc = receitas_mes_orc - despesas_mes_orc
                                
                                # Aplicar operador matemático
                                if conta_n2.operation_type == '+':
                                    valor_mes_real = abs(valor_mes_real)
                                    valor_mes_orc = abs(valor_mes_orc)
                                elif conta_n2.operation_type == '-':
                                    valor_mes_real = -abs(valor_mes_real)
                                    valor_mes_orc = -abs(valor_mes_orc)
                                
                                classificacao_item["valores_mensais"][mes] = valor_mes_real
                                classificacao_item["orcamentos_mensais"][mes] = valor_mes_orc
                            
                            for tri in trimestres:
                                df_class_tri_real = df_conta_real[df_conta_real['trimestre'] == tri]
                                df_class_tri_orc = df_conta_orc[df_conta_orc['trimestre'] == tri]
                                
                                # Realizado
                                receitas_tri_real = float(df_class_tri_real[df_class_tri_real['type'] == 'receita']['value'].sum())
                                despesas_tri_real = float(df_class_tri_real[df_class_tri_real['type'] == 'despesa']['value'].sum())
                                valor_tri_real = receitas_tri_real - despesas_tri_real
                                
                                # Orçamento
                                receitas_tri_orc = float(df_class_tri_orc[df_class_tri_orc['type'] == 'receita']['value'].sum())
                                despesas_tri_orc = float(df_class_tri_orc[df_class_tri_orc['type'] == 'despesa']['value'].sum())
                                valor_tri_orc = receitas_tri_orc - despesas_tri_orc
                                
                                # Aplicar operador matemático
                                if conta_n2.operation_type == '+':
                                    valor_tri_real = abs(valor_tri_real)
                                    valor_tri_orc = abs(valor_tri_orc)
                                elif conta_n2.operation_type == '-':
                                    valor_tri_real = -abs(valor_tri_real)
                                    valor_tri_orc = -abs(valor_tri_orc)
                                
                                classificacao_item["valores_trimestrais"][tri] = valor_tri_real
                                classificacao_item["orcamentos_trimestrais"][tri] = valor_tri_orc
                            
                            for ano in anos:
                                df_class_ano_real = df_conta_real[df_conta_real['ano'] == ano]
                                df_class_ano_orc = df_conta_orc[df_conta_orc['ano'] == ano]
                                
                                # Realizado
                                receitas_ano_real = float(df_class_ano_real[df_class_ano_real['type'] == 'receita']['value'].sum())
                                despesas_ano_real = float(df_class_ano_real[df_class_ano_real['type'] == 'despesa']['value'].sum())
                                valor_ano_real = receitas_ano_real - despesas_ano_real
                                
                                # Orçamento
                                receitas_ano_orc = float(df_class_ano_orc[df_class_ano_orc['type'] == 'receita']['value'].sum())
                                despesas_ano_orc = float(df_class_ano_orc[df_class_ano_orc['type'] == 'despesa']['value'].sum())
                                valor_ano_orc = receitas_ano_orc - despesas_ano_orc
                                
                                # Aplicar operador matemático
                                if conta_n2.operation_type == '+':
                                    valor_ano_real = abs(valor_ano_real)
                                    valor_ano_orc = abs(valor_ano_orc)
                                elif conta_n2.operation_type == '-':
                                    valor_ano_real = -abs(valor_ano_real)
                                    valor_ano_orc = -abs(valor_ano_orc)
                                
                                classificacao_item["valores_anuais"][str(ano)] = valor_ano_real
                                classificacao_item["orcamentos_anuais"][str(ano)] = valor_ano_orc
                            
                            conta_n2_item["classificacoes"].append(classificacao_item)
                    
                    # Adicionar conta DRE N2 como classificação do totalizador
                    totalizador_item["classificacoes"].append(conta_n2_item)
                
                # Calcular valor total do totalizador
                totalizador_item["valor"] = float(sum(totalizador_item["valores_mensais"].values()))
                totalizador_item["orcamento_total"] = float(sum(totalizador_item["orcamentos_mensais"].values()))
                
                # Adicionar totalizador ao resultado
                result.append(totalizador_item)
            
            return {
                "success": True,
                "meses": [str(mes) for mes in meses],
                "trimestres": [str(tri) for tri in trimestres],
                "anos": [str(ano) for ano in anos],
                "data": result
            }
            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Erro no DRE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar DRE: {str(e)}")

async def get_dre_basic_structure(df, meses, trimestres, anos):
    """Estrutura DRE básica quando não há estruturas migradas"""
    # Processar dados para DRE básico
    df['date'] = pd.to_datetime(df['date'])
    df['mes'] = df['date'].dt.strftime('%Y-%m')
    df['ano'] = df['date'].dt.year
    df['trimestre'] = df['date'].dt.to_period('Q').astype(str)
    
    # Períodos únicos
    meses = sorted(df['mes'].unique())
    anos = sorted(df['ano'].unique())
    trimestres = sorted(df['trimestre'].unique())
    
    # Calcular valores reais
    receitas_total = float(df[df['type'] == 'receita']['value'].sum())
    despesas_total = float(df[df['type'] == 'despesa']['value'].sum())
    
    # Calcular valores por período
    receitas_mensais = {}
    despesas_mensais = {}
    for mes in meses:
        df_mes = df[df['mes'] == mes]
        receitas_mensais[mes] = float(df_mes[df_mes['type'] == 'receita']['value'].sum())
        despesas_mensais[mes] = float(df_mes[df_mes['type'] == 'despesa']['value'].sum())
    
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
