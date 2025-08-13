"""
Repository pattern para operações com dados financeiros usando SQLAlchemy
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import FinancialData, Category, Period, User, Role, Permission, UserRole, RolePermission

class FinancialDataRepository:
    """Repository para operações com dados financeiros"""
    
    def get_financial_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        data_type: Optional[str] = None,
        is_budget: Optional[bool] = None,
        limit: int = 100000
    ) -> List[Dict[str, Any]]:
        """Busca dados financeiros com filtros (nova estrutura baseada no Excel)"""
        
        with DatabaseSession() as session:
            query = session.query(FinancialData)
            
            # Aplicar filtros usando as novas colunas
            if start_date:
                query = query.filter(FinancialData.data >= start_date)
            if end_date:
                query = query.filter(FinancialData.data <= end_date)
            if category:
                # Buscar tanto em DFC quanto DRE
                query = query.filter(
                    (FinancialData.dfc_n1.like(f"%{category}%")) |
                    (FinancialData.dre_n1.like(f"%{category}%"))
                )
            
            query = query.limit(limit)
            
            results = query.all()
            return [
                {
                    'id': item.id,
                    'origem': item.origem,
                    'empresa': item.empresa,
                    'nome': item.nome,
                    'classificacao': item.classificacao,
                    'emissao': item.emissao,
                    'competencia': item.competencia,
                    'vencimento': item.vencimento,
                    'valor_original': item.valor_original,
                    'data': item.data,
                    'valor': item.valor,
                    'banco': item.banco,
                    'conta_corrente': item.conta_corrente,
                    'documento': item.documento,
                    'observacao': item.observacao,
                    'local': item.local,
                    'segmento': item.segmento,
                    'projeto': item.projeto,
                    'centro_de_resultado': item.centro_de_resultado,
                    'diretoria': item.diretoria,
                    'dre_n1': item.dre_n1,
                    'dre_n2': item.dre_n2,
                    'dfc_n1': item.dfc_n1,
                    'dfc_n2': item.dfc_n2,
                    
                    # Manter compatibilidade com código antigo
                    'category': item.dfc_n1 or item.dre_n1,
                    'subcategory': item.dfc_n2 or item.dre_n2,
                    'description': item.nome,
                    'value': item.valor,
                    'type': 'receita' if item.valor and item.valor > 0 else 'despesa',
                    'date': item.data,
                    'source': item.origem,
                    'is_budget': False,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                for item in results
            ]
    
    def get_data_by_period(
        self,
        period_type: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Dict[str, float]]:
        """Agrupa dados por período (mensal, trimestral, anual)"""
        
        with DatabaseSession() as session:
            query = session.query(FinancialData).filter(
                and_(
                    FinancialData.date >= start_date,
                    FinancialData.date <= end_date
                )
            )
            
            results = query.all()
            
            # Agrupar por período
            grouped_data = {}
            for item in results:
                period = self._get_period_key(item.date, period_type)
                category = item.category
                value = float(item.value)
                
                if period not in grouped_data:
                    grouped_data[period] = {}
                
                if category not in grouped_data[period]:
                    grouped_data[period][category] = 0.0
                
                grouped_data[period][category] += value
            
            return grouped_data
    
    def get_categories_hierarchy(self) -> List[Dict[str, Any]]:
        """Busca hierarquia de categorias"""
        
        with DatabaseSession() as session:
            categories = session.query(Category).filter(Category.is_active == True).all()
            
            # Organizar em hierarquia
            return self._build_hierarchy(categories)
    
    def insert_financial_data(self, data: Dict[str, Any]) -> int:
        """Insere novo dado financeiro"""
        
        with DatabaseSession() as session:
            financial_data = FinancialData(**data)
            session.add(financial_data)
            session.flush()  # Para obter o ID
            return financial_data.id
    
    def update_financial_data(self, id: int, data: Dict[str, Any]) -> bool:
        """Atualiza dado financeiro"""
        
        with DatabaseSession() as session:
            financial_data = session.query(FinancialData).filter(FinancialData.id == id).first()
            if not financial_data:
                return False
            
            for key, value in data.items():
                setattr(financial_data, key, value)
            
            financial_data.updated_at = datetime.now()
            return True
    
    def delete_financial_data(self, id: int) -> bool:
        """Remove dado financeiro"""
        
        with DatabaseSession() as session:
            financial_data = session.query(FinancialData).filter(FinancialData.id == id).first()
            if not financial_data:
                return False
            
            session.delete(financial_data)
            return True
    
    def get_summary_by_type(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, float]:
        """Resumo por tipo (receita, despesa, investimento)"""
        
        with DatabaseSession() as session:
            results = session.query(
                FinancialData.type,
                func.sum(FinancialData.value).label('total')
            ).filter(
                and_(
                    FinancialData.date >= start_date,
                    FinancialData.date <= end_date
                )
            ).group_by(FinancialData.type).all()
            
            return {result.type: float(result.total) for result in results}
    
    def get_available_months(self) -> List[str]:
        """Busca meses disponíveis nos dados"""
        
        with DatabaseSession() as session:
            results = session.query(
                func.date_trunc('month', FinancialData.date).label('month')
            ).distinct().order_by(
                func.date_trunc('month', FinancialData.date)
            ).all()
            
            return [result.month.strftime('%Y-%m') for result in results]
    
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
    
    def _build_hierarchy(self, categories: List[Category]) -> List[Dict[str, Any]]:
        """Constrói hierarquia de categorias"""
        # Criar dicionário por ID
        categories_dict = {cat.id: {
            'id': cat.id,
            'name': cat.name,
            'code': cat.code,
            'level': cat.level,
            'is_active': cat.is_active,
            'created_at': cat.created_at,
            'children': []
        } for cat in categories}
        
        # Organizar hierarquia
        root_categories = []
        for cat in categories:
            if cat.parent_id is None:
                root_categories.append(categories_dict[cat.id])
            else:
                parent = categories_dict.get(cat.parent_id)
                if parent:
                    parent['children'].append(categories_dict[cat.id])
        
        return root_categories

class UserRepository:
    """Repository para operações com usuários"""
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        
        with DatabaseSession() as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            return {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'password_hash': user.password_hash,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
    
    def get_user_roles(self, user_id: int) -> List[str]:
        """Busca roles de um usuário"""
        
        with DatabaseSession() as session:
            roles = session.query(Role).join(
                UserRole, Role.id == UserRole.role_id
            ).filter(UserRole.user_id == user_id).all()
            
            return [role.name for role in roles]
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Busca permissões de um usuário"""
        
        with DatabaseSession() as session:
            permissions = session.query(Permission).join(
                RolePermission, Permission.id == RolePermission.permission_id
            ).join(
                UserRole, RolePermission.role_id == UserRole.role_id
            ).filter(UserRole.user_id == user_id).all()
            
            return [perm.name for perm in permissions]
