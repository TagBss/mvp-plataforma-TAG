"""
Helper para funções de paginação do DRE N0
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Connection

class PaginationHelper:
    """Helper para operações de paginação do DRE N0"""
    
    @staticmethod
    def fetch_paginated_dre_structure(connection: Connection, page: int, page_size: int, 
                                    search: str = None, order_by: str = "ordem") -> Tuple[List[Dict], int]:
        """Busca dados da DRE N0 com paginação"""
        
        # Query base com filtros
        base_query = """
            SELECT 
                id as dre_n0_id,
                name as nome_conta,
                operation_type as tipo_operacao,
                order_index as ordem,
                description as descricao,
                dre_niveis as niveis
            FROM dre_structure_n0 
            WHERE is_active = true
        """
        
        # Adicionar filtro de busca se fornecido
        params = {}
        if search:
            base_query += " AND (name ILIKE :search OR description ILIKE :search)"
            params['search'] = f"%{search}%"
        
        # Adicionar ordenação
        if order_by == "nome":
            base_query += " ORDER BY name"
        elif order_by == "tipo_operacao":
            base_query += " ORDER BY operation_type, order_index"
        else:
            base_query += " ORDER BY order_index"
        
        # Query para contar total
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
        
        # Query para dados paginados
        data_query = f"{base_query} LIMIT :page_size OFFSET :offset"
        
        # Executar query de contagem
        count_result = connection.execute(text(count_query), params)
        total_items = count_result.scalar()
        
        # Calcular offset
        offset = (page - 1) * page_size
        
        # Executar query de dados
        params.update({'page_size': page_size, 'offset': offset})
        data_result = connection.execute(text(data_query), params)
        rows = data_result.fetchall()
        
        # Processar dados
        dre_items = []
        for row in rows:
            dre_items.append({
                "dre_n0_id": row.dre_n0_id,
                "nome_conta": row.nome_conta,
                "tipo_operacao": row.tipo_operacao,
                "ordem": row.ordem,
                "descricao": row.descricao,
                "niveis": row.niveis
            })
        
        return dre_items, total_items
    
    @staticmethod
    def create_pagination_metadata(page: int, page_size: int, total_items: int) -> Dict[str, Any]:
        """Cria metadados de paginação"""
        total_pages = (total_items + page_size - 1) // page_size
        
        return {
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_items": total_items,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    
    @staticmethod
    def apply_pagination_to_dre_items(dre_items: List[Dict], page: int, page_size: int, 
                                    include_all: bool = False) -> Tuple[List[Dict], Dict[str, Any]]:
        """Aplica paginação aos itens DRE"""
        total_items = len(dre_items)
        
        if include_all:
            dados_paginados = dre_items
            current_page = 1
            current_page_size = total_items
        else:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            dados_paginados = dre_items[start_idx:end_idx]
            current_page = page
            current_page_size = len(dados_paginados)
        
        pagination_meta = PaginationHelper.create_pagination_metadata(
            current_page, current_page_size, total_items
        )
        
        return dados_paginados, pagination_meta
