"""
Schema do banco de dados usando Drizzle ORM
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from drizzle_orm import (
    pg_table, varchar, integer, decimal, date as pg_date, 
    timestamp, text, boolean, index
)
from drizzle_orm.drizzle import Drizzle

# Tabela principal de dados financeiros
financial_data = pg_table(
    "financial_data",
    integer("id").primary_key().auto_increment(),
    varchar("category", length=100).not_null(),
    varchar("subcategory", length=100),
    varchar("description", length=255),
    decimal("value", precision=15, scale=2).not_null(),
    varchar("type", length=50).not_null(),  # 'receita', 'despesa', 'investimento'
    pg_date("date").not_null(),
    varchar("period", length=20),  # 'mensal', 'trimestral', 'anual'
    varchar("source", length=100),  # fonte dos dados
    boolean("is_budget").default(False),  # se é orçado ou realizado
    timestamp("created_at").default(datetime.now()),
    timestamp("updated_at").default(datetime.now()),
)

# Tabela de categorias hierárquicas
categories = pg_table(
    "categories",
    integer("id").primary_key().auto_increment(),
    varchar("name", length=100).not_null(),
    varchar("code", length=50).unique(),
    integer("parent_id").references(lambda: categories.id),
    integer("level").not_null().default(1),  # nível na hierarquia
    boolean("is_active").default(True),
    timestamp("created_at").default(datetime.now()),
)

# Tabela de períodos financeiros
periods = pg_table(
    "periods",
    integer("id").primary_key().auto_increment(),
    varchar("name", length=50).not_null(),  # '2024-01', '2024-Q1', '2024'
    varchar("type", length=20).not_null(),  # 'month', 'quarter', 'year'
    pg_date("start_date").not_null(),
    pg_date("end_date").not_null(),
    boolean("is_closed").default(False),
    timestamp("created_at").default(datetime.now()),
)

# Tabela de usuários (para autenticação)
users = pg_table(
    "users",
    integer("id").primary_key().auto_increment(),
    varchar("email", length=255).unique().not_null(),
    varchar("username", length=100).unique().not_null(),
    varchar("password_hash", length=255).not_null(),
    boolean("is_active").default(True),
    timestamp("created_at").default(datetime.now()),
    timestamp("updated_at").default(datetime.now()),
)

# Tabela de roles
roles = pg_table(
    "roles",
    integer("id").primary_key().auto_increment(),
    varchar("name", length=50).unique().not_null(),
    varchar("description", length=255),
    timestamp("created_at").default(datetime.now()),
)

# Tabela de permissões
permissions = pg_table(
    "permissions",
    integer("id").primary_key().auto_increment(),
    varchar("name", length=100).unique().not_null(),
    varchar("description", length=255),
    varchar("resource", length=100).not_null(),  # 'financial_data', 'reports', etc.
    varchar("action", length=50).not_null(),  # 'read', 'write', 'delete'
    timestamp("created_at").default(datetime.now()),
)

# Tabela de relacionamento user-role
user_roles = pg_table(
    "user_roles",
    integer("id").primary_key().auto_increment(),
    integer("user_id").references(lambda: users.id).not_null(),
    integer("role_id").references(lambda: roles.id).not_null(),
    timestamp("created_at").default(datetime.now()),
)

# Tabela de relacionamento role-permission
role_permissions = pg_table(
    "role_permissions",
    integer("id").primary_key().auto_increment(),
    integer("role_id").references(lambda: roles.id).not_null(),
    integer("permission_id").references(lambda: permissions.id).not_null(),
    timestamp("created_at").default(datetime.now()),
)

# Índices para performance
financial_data_date_idx = index("financial_data_date_idx").on(financial_data.date)
financial_data_category_idx = index("financial_data_category_idx").on(financial_data.category)
financial_data_type_idx = index("financial_data_type_idx").on(financial_data.type)
financial_data_period_idx = index("financial_data_period_idx").on(financial_data.period)

categories_parent_idx = index("categories_parent_idx").on(categories.parent_id)
categories_level_idx = index("categories_level_idx").on(categories.level)

periods_type_idx = index("periods_type_idx").on(periods.type)
periods_date_range_idx = index("periods_date_range_idx").on(periods.start_date, periods.end_date)

users_email_idx = index("users_email_idx").on(users.email)
