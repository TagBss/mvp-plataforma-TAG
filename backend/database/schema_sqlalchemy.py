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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    description = Column(String(255))
    value = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)  # 'receita', 'despesa', 'investimento'
    date = Column(Date, nullable=False)
    period = Column(String(20))  # 'mensal', 'trimestral', 'anual'
    source = Column(String(100))  # fonte dos dados
    is_budget = Column(Boolean, default=False)  # se é orçado ou realizado
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

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
    parent = relationship("Category", remote_side=[id])
    children = relationship("Category")

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

# Índices para performance
Index('financial_data_date_idx', FinancialData.date)
Index('financial_data_category_idx', FinancialData.category)
Index('financial_data_type_idx', FinancialData.type)
Index('financial_data_period_idx', FinancialData.period)

Index('categories_parent_idx', Category.parent_id)
Index('categories_level_idx', Category.level)

Index('periods_type_idx', Period.type)
Index('periods_date_range_idx', Period.start_date, Period.end_date)

Index('users_email_idx', User.email)
