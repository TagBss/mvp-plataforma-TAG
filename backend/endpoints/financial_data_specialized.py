"""
Endpoints específicos para dados financeiros baseados na estrutura real da financial_data
Compatível com a estrutura das rotas Excel, mas usando PostgreSQL
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import traceback

from database.repository_specialized import SpecializedFinancialRepository

router = APIRouter(prefix="/financial-data", tags=["financial-data-specialized"])

# Dependency
def get_specialized_repository() -> SpecializedFinancialRepository:
    return SpecializedFinancialRepository()

@router.get("/dfc")
async def get_dfc_data(
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    repository: SpecializedFinancialRepository = Depends(get_specialized_repository)
):
    """
    Endpoint DFC (Demonstração de Fluxo de Caixa) - PostgreSQL
    
    Retorna a estrutura DFC baseada nos dados reais da financial_data,
    mantendo compatibilidade com a versão Excel.
    """
    
    try:
        print(f"🔍 DFC PostgreSQL - Iniciando processamento")
        print(f"📅 Período: {start_date} até {end_date}")
        
        # Usar datas padrão se não fornecidas
        if not start_date:
            start_date = date(2023, 1, 1)
        if not end_date:
            end_date = date(2025, 12, 31)
        
        result = repository.get_dfc_data(
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✅ DFC processado com sucesso")
        print(f"📊 Períodos: {len(result.get('meses', []))} meses, {len(result.get('data', []))} itens")
        
        return result
        
    except Exception as e:
        error_msg = f"Erro ao processar DFC: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/dre")
async def get_dre_data(
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    mes: Optional[str] = Query(None, description="Filtro por mês (YYYY-MM)"),
    repository: SpecializedFinancialRepository = Depends(get_specialized_repository)
):
    """
    Endpoint DRE (Demonstração do Resultado do Exercício) - PostgreSQL
    
    Retorna a estrutura DRE baseada nos dados reais da financial_data,
    mantendo compatibilidade com a versão Excel.
    """
    
    try:
        print(f"🔍 DRE PostgreSQL - Iniciando processamento")
        print(f"📅 Período: {start_date} até {end_date}")
        print(f"📅 Mês específico: {mes}")
        
        # Aplicar filtro por mês se fornecido
        if mes:
            try:
                year, month = map(int, mes.split('-'))
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
                print(f"📅 Período ajustado pelo mês: {start_date} até {end_date}")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de mês inválido. Use YYYY-MM")
        
        # Usar datas padrão se não fornecidas
        if not start_date:
            start_date = date(2023, 1, 1)
        if not end_date:
            end_date = date(2025, 12, 31)
        
        result = repository.get_dre_data(
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✅ DRE processado com sucesso")
        print(f"📊 Períodos: {len(result.get('meses', []))} meses, {len(result.get('data', []))} itens")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Erro ao processar DRE: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/receber")
async def get_receber_data(
    mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM"),
    repository: SpecializedFinancialRepository = Depends(get_specialized_repository)
):
    """
    Endpoint para contas a receber - PostgreSQL
    
    Retorna dados de contas a receber com análises MoM,
    mantendo compatibilidade com a versão Excel.
    """
    
    try:
        print(f"🔍 Contas a Receber PostgreSQL - Processando")
        print(f"📅 Mês específico: {mes}")
        
        result = repository.get_receber_data(mes=mes)
        
        print(f"✅ Contas a receber processadas com sucesso")
        print(f"💰 Saldo total: R$ {result.get('data', {}).get('saldo_total', 0):,.2f}")
        
        return result
        
    except Exception as e:
        error_msg = f"Erro ao processar contas a receber: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/pagar")
async def get_pagar_data(
    mes: Optional[str] = Query(None, description="Mês no formato YYYY-MM"),
    repository: SpecializedFinancialRepository = Depends(get_specialized_repository)
):
    """
    Endpoint para contas a pagar - PostgreSQL
    
    Retorna dados de contas a pagar com análises MoM,
    mantendo compatibilidade com a versão Excel.
    """
    
    try:
        print(f"🔍 Contas a Pagar PostgreSQL - Processando")
        print(f"📅 Mês específico: {mes}")
        
        result = repository.get_pagar_data(mes=mes)
        
        print(f"✅ Contas a pagar processadas com sucesso")
        print(f"💰 Saldo total: R$ {result.get('data', {}).get('saldo_total', 0):,.2f}")
        
        return result
        
    except Exception as e:
        error_msg = f"Erro ao processar contas a pagar: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/summary-specialized")
async def get_specialized_summary(
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    repository: SpecializedFinancialRepository = Depends(get_specialized_repository)
):
    """
    Endpoint para resumo especializado dos dados financeiros
    
    Retorna um resumo consolidado das estruturas DFC e DRE.
    """
    
    try:
        print(f"🔍 Resumo Especializado - Processando")
        
        # Usar datas padrão se não fornecidas
        if not start_date:
            start_date = date(2023, 1, 1)
        if not end_date:
            end_date = date(2025, 12, 31)
        
        # Buscar dados DFC e DRE
        dfc_data = repository.get_dfc_data(start_date=start_date, end_date=end_date)
        dre_data = repository.get_dre_data(start_date=start_date, end_date=end_date)
        receber_data = repository.get_receber_data()
        pagar_data = repository.get_pagar_data()
        
        # Montar resumo consolidado
        summary = {
            "periodo": {
                "start_date": start_date,
                "end_date": end_date
            },
            "dfc": {
                "success": dfc_data.get("success", False),
                "total_periodos": len(dfc_data.get("meses", [])),
                "total_estruturas": len(dfc_data.get("data", []))
            },
            "dre": {
                "success": dre_data.get("success", False),
                "total_periodos": len(dre_data.get("meses", [])),
                "total_estruturas": len(dre_data.get("data", []))
            },
            "receber": {
                "success": receber_data.get("success", False),
                "saldo_total": receber_data.get("data", {}).get("saldo_total", 0),
                "meses_disponiveis": len(receber_data.get("data", {}).get("meses_disponiveis", []))
            },
            "pagar": {
                "success": pagar_data.get("success", False),
                "saldo_total": pagar_data.get("data", {}).get("saldo_total", 0),
                "meses_disponiveis": len(pagar_data.get("data", {}).get("meses_disponiveis", []))
            },
            "timestamp": datetime.now()
        }
        
        print(f"✅ Resumo especializado processado com sucesso")
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        error_msg = f"Erro ao processar resumo especializado: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/health-specialized")
async def health_check_specialized():
    """
    Verifica saúde das rotas especializadas
    """
    
    try:
        repository = SpecializedFinancialRepository()
        
        # Testar DFC
        dfc_test = repository.get_dfc_data(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Testar DRE
        dre_test = repository.get_dre_data(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Testar Receber
        receber_test = repository.get_receber_data(mes="2024-01")
        
        # Testar Pagar
        pagar_test = repository.get_pagar_data(mes="2024-01")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "tests": {
                "dfc": dfc_test.get("success", False),
                "dre": dre_test.get("success", False),
                "receber": receber_test.get("success", False),
                "pagar": pagar_test.get("success", False)
            },
            "database_connected": True,
            "structures_available": True
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e),
            "database_connected": False,
            "structures_available": False
        }
