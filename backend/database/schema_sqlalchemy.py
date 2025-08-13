"""
Schema do banco de dados usando SQLAlchemy para PostgreSQL
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class FinancialData(Base):
    __tablename__ = "financial_data"
    
    # Estrutura baseada na aba "base" do Excel
    id = Column(Integer, primary_key=True, autoincrement=True)
    origem = Column(String(255))  # CAP, BLUEFIT, etc
    empresa = Column(String(255))  # Nome da empresa
    nome = Column(String(255))  # Nome/descrição da transação
    classificacao = Column(String(255))  # Classificação do tipo de transação
    emissao = Column(Date)  # Data de emissão
    competencia = Column(Date)  # Data de competência
    vencimento = Column(Date)  # Data de vencimento
    valor_original = Column(Float)  # Valor original
    data = Column(Date)  # Data principal
    valor = Column(Float)  # Valor principal
    banco = Column(String(255))  # Nome do banco
    conta_corrente = Column(String(255))  # Conta corrente
    documento = Column(String(255))  # Número do documento
    observacao = Column(Text)  # Observações
    local = Column(String(255))  # Local
    segmento = Column(String(255))  # Segmento
    projeto = Column(String(255))  # Projeto
    centro_de_resultado = Column(String(255))  # Centro de resultado
    diretoria = Column(String(255))  # Diretoria
    dre_n1 = Column(String(255))  # DRE Nível 1
    dre_n2 = Column(String(255))  # DRE Nível 2
    dfc_n1 = Column(String(255))  # DFC Nível 1
    dfc_n2 = Column(String(255))  # DFC Nível 2

# ============================================================================
# ESTRUTURAS DFC (Fluxo de Caixa)
# ============================================================================

class DFCStructureN1(Base):
    """Estrutura hierárquica nível 1 do DFC (Totalizadores principais)"""
    __tablename__ = "dfc_structure_n1"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dfc_n1_id = Column(Integer, unique=True, nullable=False)  # ID da planilha Excel
    name = Column(String(200), nullable=False)  # Nome do totalizador
    operation_type = Column(String(10), default="=")  # Tipo de operação: +, -, =, +/-
    description = Column(Text)
    order_index = Column(Integer, default=0)  # Ordem de exibição
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    children = relationship("DFCStructureN2", back_populates="parent")

class DFCStructureN2(Base):
    """Estrutura hierárquica nível 2 do DFC (Contas específicas)"""
    __tablename__ = "dfc_structure_n2"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dfc_n2_id = Column(Integer, unique=True, nullable=False)  # ID da planilha Excel
    dfc_n1_id = Column(Integer, ForeignKey('dfc_structure_n1.dfc_n1_id'), nullable=False)
    name = Column(String(200), nullable=False)  # Nome da conta
    operation_type = Column(String(10), default="=")  # Tipo de operação: +, -, =, +/-
    description = Column(Text)
    order_index = Column(Integer, default=0)  # Ordem de exibição
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    parent = relationship("DFCStructureN1", back_populates="children")
    classifications = relationship("DFCClassification", back_populates="dfc_n2")

class DFCClassification(Base):
    """Classificações específicas dentro de cada conta DFC N2"""
    __tablename__ = "dfc_classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dfc_n2_id = Column(Integer, ForeignKey('dfc_structure_n2.dfc_n2_id'), nullable=False)
    name = Column(String(200), nullable=False)  # Nome da classificação
    description = Column(Text)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    dfc_n2 = relationship("DFCStructureN2", back_populates="classifications")

# ============================================================================
# ESTRUTURAS DRE (Demonstração de Resultados)
# ============================================================================

class DREStructureN0(Base):
    """Estrutura hierárquica nível 0 da DRE (Estrutura principal da aba 'dre')"""
    __tablename__ = "dre_structure_n0"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dre_n0_id = Column(Integer, unique=True, nullable=False)  # ID da planilha Excel
    name = Column(String(200), nullable=False)  # Nome da conta principal
    operation_type = Column(String(10), default="=")  # Tipo de operação: +, -, =, +/-
    description = Column(Text)
    order_index = Column(Integer, default=0)  # Ordem de exibição
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    children = relationship("DREStructureN1", back_populates="parent_n0")

class DREStructureN1(Base):
    """Estrutura hierárquica nível 1 da DRE (Totalizadores principais)"""
    __tablename__ = "dre_structure_n1"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dre_n1_id = Column(Integer, unique=True, nullable=False)  # ID da planilha Excel
    dre_n0_id = Column(Integer, ForeignKey('dre_structure_n0.dre_n0_id'), nullable=True)  # Relacionamento com N0
    name = Column(String(200), nullable=False)  # Nome do totalizador
    operation_type = Column(String(10), default="=")  # Tipo de operação: +, -, =, +/-
    description = Column(Text)
    order_index = Column(Integer, default=0)  # Ordem de exibição
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    parent_n0 = relationship("DREStructureN0", back_populates="children")
    children = relationship("DREStructureN2", back_populates="parent")

class DREStructureN2(Base):
    """Estrutura hierárquica nível 2 da DRE (Contas específicas)"""
    __tablename__ = "dre_structure_n2"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dre_n2_id = Column(Integer, unique=True, nullable=False)  # ID da planilha Excel
    dre_n1_id = Column(Integer, ForeignKey('dre_structure_n1.dre_n1_id'), nullable=False)
    name = Column(String(200), nullable=False)  # Nome da conta
    operation_type = Column(String(10), default="=")  # Tipo de operação: +, -, =, +/-
    description = Column(Text)
    order_index = Column(Integer, default=0)  # Ordem de exibição
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    parent = relationship("DREStructureN1", back_populates="children")
    classifications = relationship("DREClassification", back_populates="dre_n2")

class DREClassification(Base):
    """Classificações específicas dentro de cada conta DRE N2"""
    __tablename__ = "dre_classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dre_n2_id = Column(Integer, ForeignKey('dre_structure_n2.dre_n2_id'), nullable=False)
    name = Column(String(200), nullable=False)  # Nome da classificação
    description = Column(Text)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    dre_n2 = relationship("DREStructureN2", back_populates="classifications")

# ============================================================================
# TABELAS EXISTENTES (mantidas para compatibilidade)
# ============================================================================

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    level = Column(Integer, nullable=False, default=1)  # nível na hierarquia
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")

class Period(Base):
    __tablename__ = "periods"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)  # '2024-01', '2024-Q1', '2024'
    type = Column(String(20), nullable=False)  # 'month', 'quarter', 'year'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    resource = Column(String(100), nullable=False)  # 'financial_data', 'reports', etc.
    action = Column(String(50), nullable=False)  # 'read', 'write', 'delete'
    created_at = Column(DateTime, default=datetime.now)

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

# ============================================================================
# ÍNDICES PARA PERFORMANCE
# ============================================================================

# Índices para FinancialData (nova estrutura)
Index('idx_financial_data_data', FinancialData.data)
Index('idx_financial_data_dfc_n1', FinancialData.dfc_n1)
Index('idx_financial_data_dre_n1', FinancialData.dre_n1)
Index('idx_financial_data_origem', FinancialData.origem)

# Índices para estruturas DFC
Index('idx_dfc_n1_order', DFCStructureN1.order_index)
Index('idx_dfc_n2_parent', DFCStructureN2.dfc_n1_id)
Index('idx_dfc_n2_order', DFCStructureN2.order_index)
Index('idx_dfc_classification_parent', DFCClassification.dfc_n2_id)

# Índices para estruturas DRE
Index('idx_dre_n0_order', DREStructureN0.order_index)
Index('idx_dre_n0_active', DREStructureN0.is_active)
Index('idx_dre_n1_order', DREStructureN1.order_index)
Index('idx_dre_n1_parent', DREStructureN1.dre_n0_id)
Index('idx_dre_n2_parent', DREStructureN2.dre_n1_id)
Index('idx_dre_n2_order', DREStructureN2.order_index)
Index('idx_dre_classification_parent', DREClassification.dre_n2_id)
