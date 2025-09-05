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
    dfc_n1_id = Column(Integer, ForeignKey('dfc_structure_n1.id'), nullable=False)
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
    dfc_n2_id = Column(Integer, ForeignKey('dfc_structure_n2.id'), nullable=False)
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
    dre_n0_id = Column(Integer, ForeignKey('dre_structure_n0.id'), nullable=True)  # Relacionamento com N0
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
    dre_n1_id = Column(Integer, ForeignKey('dre_structure_n1.id'), nullable=False)
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
    dre_n2_id = Column(Integer, ForeignKey('dre_structure_n2.id'), nullable=False)
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
# NOVAS TABELAS DE CADASTRO E ESTRUTURA
# ============================================================================

class GrupoEmpresa(Base):
    """Grupo empresarial (ex: Bluefit T8)"""
    __tablename__ = "grupos_empresa"
    
    id = Column(String(36), primary_key=True)  # UUID
    nome = Column(String(200), nullable=False, unique=True)
    empresa_id = Column(String(36), ForeignKey('empresas.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="grupos_empresa")
    categorias = relationship("Categoria", back_populates="grupo_empresa")

class Empresa(Base):
    """Empresas específicas (ex: Bluefit)"""
    __tablename__ = "empresas"
    
    id = Column(String(36), primary_key=True)  # UUID
    nome = Column(String(200), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    grupos_empresa = relationship("GrupoEmpresa", back_populates="empresa")

class Categoria(Base):
    """Categorias de classificação (ex: Cliente, Fornecedor, etc)"""
    __tablename__ = "categorias"
    
    id = Column(String(36), primary_key=True)  # UUID
    nome = Column(String(200), nullable=False)
    grupo_empresa_id = Column(String(36), ForeignKey('grupos_empresa.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    grupo_empresa = relationship("GrupoEmpresa", back_populates="categorias")

class PlanoDeContas(Base):
    """Plano de contas da Bluefit (aba 'plano_de_contas')"""
    __tablename__ = "plano_de_contas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_empresa_id = Column(String(36), ForeignKey('grupos_empresa.id'), nullable=False)
    
    # Estrutura hierárquica
    conta_pai = Column(String(200))  # Aumentado de 50 para 200
    conta = Column(String(100), nullable=False)  # Aumentado de 50 para 100
    nome_conta = Column(String(500), nullable=False)  # Aumentado de 300 para 500
    tipo_conta = Column(String(100))  # Aumentado de 50 para 100
    nivel = Column(Integer)  # Nível na hierarquia
    ordem = Column(Integer)  # Ordem de exibição
    
    # Classificações DRE
    classificacao_dre = Column(String(200))  # DRE Nível 1
    classificacao_dre_n2 = Column(String(200))  # DRE Nível 2
    
    # Classificações DFC
    classificacao_dfc = Column(String(200))  # DFC Nível 1
    classificacao_dfc_n2 = Column(String(200))  # DFC Nível 2
    
    centro_custo = Column(String(200))  # Aumentado de 100 para 200
    
    # Metadados
    observacoes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    grupo_empresa = relationship("GrupoEmpresa")

class DePara(Base):
    """Tabela de mapeamento/de_para da Bluefit (aba 'de_para')"""
    __tablename__ = "de_para"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_empresa_id = Column(String(36), ForeignKey('grupos_empresa.id'), nullable=False)
    
    # Campos de origem e destino
    origem_sistema = Column(String(100))  # Sistema de origem
    descricao_origem = Column(String(300))  # Descrição no sistema de origem
    descricao_destino = Column(String(300))  # Descrição no sistema atual
    
    # Metadados
    observacoes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    grupo_empresa = relationship("GrupoEmpresa")

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

# Índices para novas tabelas
Index('idx_grupo_empresa_empresa', GrupoEmpresa.empresa_id)
Index('idx_categoria_grupo_empresa', Categoria.grupo_empresa_id)
Index('idx_plano_contas_grupo_empresa', PlanoDeContas.grupo_empresa_id)
Index('idx_plano_contas_conta', PlanoDeContas.conta)
Index('idx_de_para_grupo_empresa', DePara.grupo_empresa_id)
Index('idx_de_para_origem', DePara.descricao_origem)
Index('idx_de_para_destino', DePara.descricao_destino)
