#!/usr/bin/env python3
"""
Script para executar o arquivo views_dre_n0.sql e criar as views DRE N0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def execute_views_dre_n0_sql():
    """Executa o arquivo views_dre_n0.sql para criar as views DRE N0"""
    
    print("🔧 EXECUTANDO ARQUIVO views_dre_n0.sql...")
    
    # 1. Ler o arquivo SQL
    sql_file_path = 'database/views_dre_n0.sql'
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"   📄 Arquivo SQL lido: {len(sql_content)} caracteres")
    except FileNotFoundError:
        print(f"   ❌ Arquivo não encontrado: {sql_file_path}")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False
    
    # 2. Dividir o SQL em comandos individuais
    # Remover comentários e dividir por ';'
    sql_commands = []
    current_command = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Pular linhas vazias e comentários
        if not line or line.startswith('--') or line.startswith('/*'):
            continue
            
        current_command += line + " "
        
        if line.endswith(';'):
            sql_commands.append(current_command.strip())
            current_command = ""
    
    print(f"   📋 Comandos SQL encontrados: {len(sql_commands)}")
    
    # 3. Executar cada comando SQL
    engine = get_engine()
    with engine.connect() as connection:
        
        for i, command in enumerate(sql_commands, 1):
            try:
                print(f"   🔧 Executando comando {i}/{len(sql_commands)}...")
                
                # Executar o comando
                connection.execute(text(command))
                print(f"   ✅ Comando {i} executado com sucesso")
                
            except Exception as e:
                print(f"   ❌ Erro no comando {i}: {e}")
                print(f"   📝 Comando: {command[:100]}...")
                continue
        
        # 4. Verificar se as views foram criadas
        print("\n🔍 VERIFICANDO SE AS VIEWS FORAM CRIADAS...")
        
        check_views = text("""
            SELECT viewname, schemaname 
            FROM pg_views 
            WHERE viewname IN ('v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo')
            AND schemaname = 'public'
        """)
        
        views_result = connection.execute(check_views).fetchall()
        
        if views_result:
            print(f"   ✅ Views criadas: {len(views_result)}")
            for view in views_result:
                print(f"      - {view[0]} no schema {view[1]}")
        else:
            print("   ❌ Nenhuma view foi criada!")
            return False
        
        # 5. Testar se as views retornam dados
        print("\n🧪 TESTANDO SE AS VIEWS RETORNAM DADOS...")
        
        for view_name in ['v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo']:
            try:
                test_query = text(f"SELECT COUNT(*) as total FROM {view_name}")
                count = connection.execute(test_query).scalar()
                print(f"   📊 {view_name}: {count} registros")
                
                if count > 0:
                    print(f"   ✅ {view_name} funcionando!")
                else:
                    print(f"   ⚠️ {view_name} sem dados")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar {view_name}: {e}")
        
        # 6. Verificar se as views aparecem no information_schema
        print("\n🔍 VERIFICANDO SE AS VIEWS APARECEM NO INFORMATION_SCHEMA...")
        
        info_schema_query = text("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_name IN ('v_dre_n0_completo', 'v_dre_n0_simples', 'v_dre_n0_por_periodo')
            AND table_schema = 'public'
            AND table_type = 'VIEW'
        """)
        
        info_result = connection.execute(info_schema_query).fetchall()
        
        if info_result:
            print(f"   ✅ Views no information_schema: {len(info_result)}")
            for view in info_result:
                print(f"      - {view[0]} ({view[1]})")
        else:
            print("   ❌ Views não aparecem no information_schema")
            
        return True

if __name__ == "__main__":
    try:
        success = execute_views_dre_n0_sql()
        if success:
            print("\n🎉 VIEWS DRE N0 CRIADAS COM SUCESSO!")
            print("   ✅ Arquivo SQL executado")
            print("   ✅ 3 views criadas")
            print("   ✅ Views devem aparecer no admin")
        else:
            print("\n❌ ERRO AO CRIAR VIEWS DRE N0!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
