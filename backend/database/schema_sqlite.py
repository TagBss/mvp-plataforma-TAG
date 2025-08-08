"""
Schema do banco de dados usando Drizzle ORM para SQLite
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from drizzle_orm import (
    sqlite_table, text, integer, real, datetime as sqlite_datetime, 
    boolean, index
)

# Tabela principal de dados financeiros
financial_data = sqlite_table(
    "financial_data",
    integer("id").primary_key().auto_increment(),
    text("category").not_null(),
    text("subcategory"),
    text("description"),
    real("value").not_null(),
    text("type").not_null(),  # 'receita', 'despesa', 'investimento'
    sqlite_datetime("date").not_null(),
    text("period"),  # 'mensal', 'trimestral', 'anual'
    text("source"),  # fonte dos dados
    boolean("is_budget").default(False),  # se é orçado ou realizado
    sqlite_datetime("created_at").default(datetime.now()),
    sqlite_datetime("updated_at").default(datetime.now()),
)

# Tabela de categorias hierárquicas
categories = sqlite_table(
    "categories",
    integer("id").primary_key().auto_increment(),
    text("name").not_null(),
    text("code").unique(),
    integer("parent_id").references(lambda: categories.id),
    integer("level").not_null().default(1),  # nível na hierarquia
    boolean("is_active").default(True),
    sqlite_datetime("created_at").default(datetime.now()),
)

# Tabela de períodos financeiros
periods = sqlite_table(
    "periods",
    integer("id").primary_key().auto_increment(),
    text("name").not_null(),  # '2024-01', '2024-Q1', '2024'
    text("type").not_null(),  # 'month', 'quarter', 'year'
    sqlite_datetime("start_date").not_null(),
    sqlite_datetime("end_date").not_null(),
    boolean("is_closed").default(False),
    sqlite_datetime("created_at").default(datetime.now()),
)

# Tabela de usuários (para autenticação)
users = sqlite_table(
    "users",
    integer("id").primary_key().auto_increment(),
    text("email").unique().not_null(),
    text("username").unique().not_null(),
    text("password_hash").not_null(),
    boolean("is_active").default(True),
    sqlite_datetime("created_at").default(datetime.now()),
    sqlite_datetime("updated_at").default(datetime.now()),
)

# Tabela de roles
roles = sqlite_table(
    "roles",
    integer("id").primary_key().auto_increment(),
    text("name").unique().not_null(),
    text("description"),
    sqlite_datetime("created_at").default(datetime.now()),
)

# Tabela de permissões
permissions = sqlite_table(
    "permissions",
    integer("id").primary_key().auto_increment(),
    text("name").unique().not_null(),
    text("description"),
    text("resource").not_null(),  # 'financial_data', 'reports', etc.
    text("action").not_null(),  # 'read', 'write', 'delete'
    sqlite_datetime("created_at").default(datetime.now()),
)

# Tabela de relacionamento user-role
user_roles = sqlite_table(
    "user_roles",
    integer("id").primary_key().auto_increment(),
    integer("user_id").references(lambda: users.id).not_null(),
    integer("role_id").references(lambda: roles.id).not_null(),
    sqlite_datetime("created_at").default(datetime.now()),
)

# Tabela de relacionamento role-permission
role_permissions = sqlite_table(
    "role_permissions",
    integer("id").primary_key().auto_increment(),
    integer("role_id").references(lambda: roles.id).not_null(),
    integer("permission_id").references(lambda: permissions.id).not_null(),
    sqlite_datetime("created_at").default(datetime.now()),
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
