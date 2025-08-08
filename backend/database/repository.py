"""
Repository pattern para operações com dados financeiros usando Drizzle ORM
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from database.connection import get_database
from database.schema import financial_data, categories, periods, users, roles, permissions

class FinancialDataRepository:
    """Repository para operações com dados financeiros"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_financial_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        data_type: Optional[str] = None,
        is_budget: Optional[bool] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Busca dados financeiros com filtros"""
        
        query = financial_data.select()
        
        # Aplicar filtros
        if start_date:
            query = query.where(financial_data.date >= start_date)
        if end_date:
            query = query.where(financial_data.date <= end_date)
        if category:
            query = query.where(financial_data.category == category)
        if data_type:
            query = query.where(financial_data.type == data_type)
        if is_budget is not None:
            query = query.where(financial_data.is_budget == is_budget)
        
        query = query.limit(limit)
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            return [dict(row) for row in result.fetchall()]
    
    async def get_data_by_period(
        self,
        period_type: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Dict[str, Decimal]]:
        """Agrupa dados por período (mensal, trimestral, anual)"""
        
        query = financial_data.select().where(
            (financial_data.date >= start_date) &
            (financial_data.date <= end_date)
        )
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            data = result.fetchall()
            
            # Agrupar por período
            grouped_data = {}
            for row in data:
                row_dict = dict(row)
                period = self._get_period_key(row_dict['date'], period_type)
                category = row_dict['category']
                value = row_dict['value']
                
                if period not in grouped_data:
                    grouped_data[period] = {}
                
                if category not in grouped_data[period]:
                    grouped_data[period][category] = Decimal('0')
                
                grouped_data[period][category] += value
            
            return grouped_data
    
    async def get_categories_hierarchy(self) -> List[Dict[str, Any]]:
        """Busca hierarquia de categorias"""
        
        query = categories.select().where(categories.is_active == True)
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            categories_list = [dict(row) for row in result.fetchall()]
            
            # Organizar em hierarquia
            return self._build_hierarchy(categories_list)
    
    async def insert_financial_data(self, data: Dict[str, Any]) -> int:
        """Insere novo dado financeiro"""
        
        with self.db.connect() as conn:
            result = conn.execute(
                financial_data.insert().values(**data)
            )
            return result.inserted_primary_key[0]
    
    async def update_financial_data(self, id: int, data: Dict[str, Any]) -> bool:
        """Atualiza dado financeiro"""
        
        with self.db.connect() as conn:
            result = conn.execute(
                financial_data.update()
                .where(financial_data.id == id)
                .values(**data, updated_at=datetime.now())
            )
            return result.rowcount > 0
    
    async def delete_financial_data(self, id: int) -> bool:
        """Remove dado financeiro"""
        
        with self.db.connect() as conn:
            result = conn.execute(
                financial_data.delete().where(financial_data.id == id)
            )
            return result.rowcount > 0
    
    async def get_summary_by_type(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Decimal]:
        """Resumo por tipo (receita, despesa, investimento)"""
        
        query = financial_data.select(
            financial_data.type,
            financial_data.value
        ).where(
            (financial_data.date >= start_date) &
            (financial_data.date <= end_date)
        )
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            data = result.fetchall()
            
            summary = {}
            for row in data:
                data_type = row[0]
                value = row[1]
                
                if data_type not in summary:
                    summary[data_type] = Decimal('0')
                
                summary[data_type] += value
            
            return summary
    
    def _get_period_key(self, date: date, period_type: str) -> str:
        """Converte data para chave de período"""
        if period_type == 'month':
            return f"{date.year}-{date.month:02d}"
        elif period_type == 'quarter':
            quarter = ((date.month - 1) // 3) + 1
            return f"{date.year}-Q{quarter}"
        elif period_type == 'year':
            return str(date.year)
        else:
            return str(date)
    
    def _build_hierarchy(self, categories_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Constrói hierarquia de categorias"""
        # Criar dicionário por ID
        categories_dict = {cat['id']: {**cat, 'children': []} for cat in categories_list}
        
        # Organizar hierarquia
        root_categories = []
        for cat in categories_list:
            if cat['parent_id'] is None:
                root_categories.append(categories_dict[cat['id']])
            else:
                parent = categories_dict.get(cat['parent_id'])
                if parent:
                    parent['children'].append(categories_dict[cat['id']])
        
        return root_categories

class UserRepository:
    """Repository para operações com usuários"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        
        query = users.select().where(users.email == email)
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            row = result.fetchone()
            return dict(row) if row else None
    
    async def get_user_roles(self, user_id: int) -> List[str]:
        """Busca roles de um usuário"""
        
        query = roles.select().join(
            user_roles, roles.id == user_roles.role_id
        ).where(user_roles.user_id == user_id)
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            return [row['name'] for row in result.fetchall()]
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Busca permissões de um usuário"""
        
        query = permissions.select().join(
            role_permissions, permissions.id == role_permissions.permission_id
        ).join(
            user_roles, role_permissions.role_id == user_roles.role_id
        ).where(user_roles.user_id == user_id)
        
        with self.db.connect() as conn:
            result = conn.execute(query)
            return [row['name'] for row in result.fetchall()]
