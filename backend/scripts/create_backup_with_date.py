#!/usr/bin/env python3
"""
Script para criar backups das tabelas e views com data no nome
Formato: nome_tabela_backup_YYYYMMDD
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

def get_connection():
    """Estabelece conexão com o banco"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='tag_financeiro',
        user='postgres',
        password='postgres'
    )

def get_tables_and_views():
    """Lista todas as tabelas e views para backup"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Buscar tabelas e views
        cur.execute("""
            SELECT 
                table_name,
                table_type,
                CASE 
                    WHEN table_type = 'BASE TABLE' THEN 'TABLE'
                    ELSE 'VIEW'
                END as object_type
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type IN ('BASE TABLE', 'VIEW')
            AND table_name NOT LIKE '%_backup_%'
            AND table_name NOT LIKE 'backup_summary_%'
            ORDER BY table_type DESC, table_name
        """)
        
        objects = cur.fetchall()
        return objects
        
    except Exception as e:
        print(f"❌ Erro ao listar tabelas e views: {e}")
        return []
    
    finally:
        cur.close()
        conn.close()

def create_backup(object_name, object_type, backup_date):
    """Cria backup de uma tabela ou view"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        backup_name = f"{object_name}_backup_{backup_date}"
        
        if object_type == 'TABLE':
            # Backup de tabela
            cur.execute(f"""
                CREATE TABLE {backup_name} AS 
                SELECT * FROM {object_name}
            """)
            print(f"  ✅ Tabela {backup_name} criada com sucesso")
        else:
            # Backup de view
            cur.execute(f"""
                CREATE TABLE {backup_name} AS 
                SELECT * FROM {object_name}
            """)
            print(f"  ✅ View {object_name} convertida para tabela {backup_name}")
        
        # Contar registros
        cur.execute(f"SELECT COUNT(*) FROM {backup_name}")
        count = cur.fetchone()[0]
        print(f"     📊 {count:,} registros copiados")
        
        return backup_name, count
        
    except Exception as e:
        print(f"  ❌ Erro ao criar backup de {object_name}: {e}")
        return None, 0
    
    finally:
        cur.close()
        conn.close()

def create_backup_summary(backups_info, backup_date):
    """Cria tabela de resumo dos backups"""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        summary_table = f"backup_summary_{backup_date}"
        
        # Criar tabela de resumo
        cur.execute(f"""
            CREATE TABLE {summary_table} (
                id SERIAL PRIMARY KEY,
                backup_name VARCHAR(255),
                original_object VARCHAR(255),
                object_type VARCHAR(50),
                record_count INTEGER,
                backup_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir informações dos backups
        for backup_name, original_object, object_type, record_count in backups_info:
            cur.execute(f"""
                INSERT INTO {summary_table} 
                (backup_name, original_object, object_type, record_count, backup_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (backup_name, original_object, object_type, record_count, backup_date))
        
        conn.commit()
        print(f"  ✅ Tabela de resumo {summary_table} criada com sucesso")
        return summary_table
        
    except Exception as e:
        print(f"  ❌ Erro ao criar tabela de resumo: {e}")
        conn.rollback()
        return None
    
    finally:
        cur.close()
        conn.close()

def main():
    """Função principal"""
    print("🔄 CRIANDO BACKUPS DAS TABELAS E VIEWS...")
    print("=" * 60)
    
    # Data de hoje
    today = datetime.now()
    backup_date = today.strftime("%Y%m%d")
    backup_date_formatted = today.strftime("%d/%m/%Y")
    
    print(f"📅 Data do backup: {backup_date_formatted} ({backup_date})")
    print()
    
    # Listar objetos para backup
    print("🔍 LISTANDO OBJETOS PARA BACKUP...")
    objects = get_tables_and_views()
    
    if not objects:
        print("❌ Nenhuma tabela ou view encontrada para backup")
        return
    
    print(f"📋 Encontrados {len(objects)} objetos:")
    for obj in objects:
        print(f"  - {obj['table_name']} ({obj['object_type']})")
    
    print()
    print("🔄 INICIANDO PROCESSO DE BACKUP...")
    
    # Criar backups
    backups_info = []
    total_objects = len(objects)
    successful_backups = 0
    
    for i, obj in enumerate(objects, 1):
        object_name = obj['table_name']
        object_type = obj['object_type']
        
        print(f"\n{i}/{total_objects} - Criando backup de {object_name} ({object_type})...")
        
        backup_name, record_count = create_backup(object_name, object_type, backup_date)
        
        if backup_name:
            backups_info.append((backup_name, object_name, object_type, record_count))
            successful_backups += 1
    
    print()
    print("📊 RESUMO DOS BACKUPS CRIADOS:")
    print("=" * 60)
    
    if backups_info:
        # Criar tabela de resumo
        print("\n🔄 CRIANDO TABELA DE RESUMO...")
        summary_table = create_backup_summary(backups_info, backup_date)
        
        if summary_table:
            print(f"\n✅ BACKUP CONCLUÍDO COM SUCESSO!")
            print(f"📅 Data: {backup_date_formatted}")
            print(f"📦 Total de backups: {successful_backups}/{total_objects}")
            print(f"📊 Tabela de resumo: {summary_table}")
            
            print(f"\n📋 BACKUPS CRIADOS:")
            for backup_name, original_object, object_type, record_count in backups_info:
                print(f"  ✅ {backup_name} ({original_object}) - {record_count:,} registros")
            
            print(f"\n🔗 Acesse a interface admin para gerenciar os backups:")
            print(f"   http://localhost:8000/admin/backups")
            
        else:
            print("❌ Erro ao criar tabela de resumo")
    else:
        print("❌ Nenhum backup foi criado com sucesso")
    
    print()
    print("🎉 PROCESSO FINALIZADO!")

if __name__ == "__main__":
    main()
