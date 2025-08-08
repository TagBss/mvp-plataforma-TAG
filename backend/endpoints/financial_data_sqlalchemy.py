"""
Endpoints para dados financeiros usando PostgreSQL e SQLAlchemy
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from decimal import Decimal

from database.repository_sqlalchemy import FinancialDataRepository
from database.connection_sqlalchemy import DatabaseSession

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
    """Atualiza registro financeiro"""
    
    try:
        # Filtrar apenas campos não nulos
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now()
        
        success = repository.update_financial_data(data_id, update_data)
        
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
    """Verifica saúde do endpoint de dados financeiros"""
    
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
