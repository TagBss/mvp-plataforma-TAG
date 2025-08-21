#!/usr/bin/env python3
"""
Script para testar a função create_dre_n0_view diretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_sqlalchemy import get_engine
from helpers_postgresql.dre.dre_n0_helper import DreN0Helper
from sqlalchemy import text

def test_create_view_directly():
    """Testa a função create_dre_n0_view diretamente"""
    
    print("🧪 TESTANDO CRIAÇÃO DA VIEW DRE N0 DIRETAMENTE...")
    
    try:
        # 1. Conectar ao banco
        print("\n🔌 1. CONECTANDO AO BANCO:")
        engine = get_engine()
        print("   ✅ Conexão estabelecida")
        
        with engine.connect() as connection:
            # 2. Verificar se a view existe
            print("\n🔍 2. VERIFICANDO VIEW EXISTENTE:")
            view_exists = DreN0Helper.check_view_exists(connection)
            print(f"   📊 View existe: {view_exists}")
            
            # 3. Tentar criar a view
            print("\n🏗️ 3. TENTANDO CRIAR VIEW:")
            try:
                success = DreN0Helper.create_dre_n0_view(connection)
                print(f"   📊 Resultado: {success}")
                
                if success:
                    print("   ✅ View criada com sucesso!")
                else:
                    print("   ❌ Falha ao criar view")
                    
            except Exception as e:
                print(f"   ❌ Erro ao criar view: {e}")
                import traceback
                traceback.print_exc()
            
            # 4. Verificar se a view foi criada
            print("\n🔍 4. VERIFICANDO SE VIEW FOI CRIADA:")
            view_exists_after = DreN0Helper.check_view_exists(connection)
            print(f"   📊 View existe após criação: {view_exists_after}")
            
            # 5. Testar query simples na view
            if view_exists_after:
                print("\n📊 5. TESTANDO QUERY NA VIEW:")
                try:
                    test_query = text("SELECT COUNT(*) FROM v_dre_n0_completo")
                    result = connection.execute(test_query)
                    count = result.scalar()
                    print(f"   📊 Total de registros: {count}")
                    print("   ✅ View funcionando!")
                except Exception as e:
                    print(f"   ❌ Erro ao consultar view: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("   ❌ View não foi criada")
        
        return True
        
    except Exception as e:
        print(f'❌ Erro geral: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_create_view_directly()
        if success:
            print("\n🎯 TESTE CONCLUÍDO!")
        else:
            print("\n❌ ERRO NO TESTE!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
