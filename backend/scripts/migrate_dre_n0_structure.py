#!/usr/bin/env python3
"""
Script para migrar estrutura DRE N0 (aba 'dre') do Excel para PostgreSQL
Seguindo o padrão dos outros scripts de migração
"""
import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from database.schema_sqlalchemy import DREStructureN0, Base

def extrair_nome_conta(texto):
    """Extrai nome da conta removendo operadores e formatação"""
    if pd.isna(texto):
        return ""
    
    texto = str(texto).strip()
    
    # Remover operadores entre parênteses no início: ( + ), ( - ), ( = ), ( +/- )
    if texto.startswith('('):
        # Encontrar o fechamento do parêntese
        end_paren = texto.find(')')
        if end_paren != -1:
            # Remover tudo até o fechamento do parêntese + espaço
            texto = texto[end_paren + 1:].strip()
    
    # Remover parênteses extras que possam ter sobrado
    texto = texto.replace('(', '').replace(')', '').strip()
    
    return texto

def extrair_tipo_operacao(texto):
    """Extrai tipo de operação baseado no texto entre parênteses"""
    if pd.isna(texto):
        return "="
    
    texto = str(texto).strip()
    
    # Procurar por operadores entre parênteses
    if '( + )' in texto:
        return "+"
    elif '( - )' in texto:
        return "-"
    elif '( = )' in texto:
        return "="
    elif '( +/- )' in texto:
        return "+/-"
    else:
        # Fallback: procurar por operadores simples
        if texto.startswith('+'):
            return "+"
        elif texto.startswith('-'):
            return "-"
        elif texto.startswith('='):
            return "="
        elif texto.startswith('+/-'):
            return "+/-"
        else:
            return "="

def migrate_dre_n0_structure():
    """Migrar estrutura DRE N0 do Excel para PostgreSQL"""
    print("🚀 MIGRAÇÃO DA ESTRUTURA DRE N0 (aba 'dre') PARA POSTGRESQL")
    print("=" * 70)
    
    # Arquivo Excel
    filename = "db_bluefit - Copia.xlsx"
    
    if not os.path.exists(filename):
        print(f"❌ Arquivo {filename} não encontrado")
        print("   Certifique-se de que o arquivo está no diretório backend/")
        return False
    
    try:
        # Carregar estrutura do Excel - aba 'dre'
        print("📥 Carregando aba 'dre' do Excel...")
        df_dre = pd.read_excel(filename, sheet_name="dre")
        
        if df_dre.empty:
            print("❌ Aba 'dre' está vazia ou não existe")
            return False
        
        print(f"📊 Dados carregados: {len(df_dre)} linhas, {len(df_dre.columns)} colunas")
        print(f"📋 Colunas disponíveis: {list(df_dre.columns)}")
        
        # Obter engine do banco
        engine = get_engine()
        if not engine:
            print("❌ Não foi possível conectar ao banco de dados")
            return False
        
        # Criar tabelas se não existirem
        print("🏗️  Criando tabelas no banco...")
        Base.metadata.create_all(engine)
        
        # Criar sessão
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Limpar estrutura DRE N0 existente
            print("🗑️  Limpando estrutura DRE N0 existente...")
            session.query(DREStructureN0).delete()
            session.commit()
            
            # Migrar estrutura DRE N0
            print("📊 Migrando estrutura DRE N0...")
            inserted_count = 0
            
            for index, row in df_dre.iterrows():
                try:
                    # Identificar colunas (pode variar dependendo do Excel)
                    dre_id = None
                    dre_name = None
                    
                    # Tentar diferentes nomes de colunas
                    if 'dre_id' in df_dre.columns:
                        dre_id = row.get('dre_id', index + 1)
                    elif 'id' in df_dre.columns:
                        dre_id = row.get('id', index + 1)
                    else:
                        dre_id = index + 1
                    
                    if 'dre' in df_dre.columns:
                        dre_name = row.get('dre', '')
                    elif 'name' in df_dre.columns:
                        dre_name = row.get('name', '')
                    elif 'conta' in df_dre.columns:
                        dre_name = row.get('conta', '')
                    else:
                        # Usar primeira coluna que não seja ID
                        for col in df_dre.columns:
                            if col.lower() not in ['id', 'dre_id', 'dre_n0_id']:
                                dre_name = row.get(col, '')
                                break
                    
                    if pd.notna(dre_name) and str(dre_name).strip():
                        nome = extrair_nome_conta(dre_name)
                        tipo = extrair_tipo_operacao(dre_name)
                        
                        # Verificar se dre_id é válido
                        if pd.isna(dre_id) or dre_id is None:
                            dre_id = index + 1
                        
                        # Converter para int Python
                        try:
                            dre_id = int(dre_id)
                        except (ValueError, TypeError):
                            dre_id = index + 1
                        
                        # Verificar se dre_id não é muito grande
                        if dre_id > 999999:
                            print(f"    ⚠️  Pulando {nome} - ID muito grande: {dre_id}")
                            continue
                        
                        dre_n0 = DREStructureN0(
                            dre_n0_id=dre_id,
                            name=nome,
                            operation_type=tipo,
                            order_index=index + 1,  # Usar índice sequencial
                            description=f"Conta DRE N0: {nome}",
                            is_active=True,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        session.add(dre_n0)
                        inserted_count += 1
                        
                        if inserted_count % 10 == 0:
                            print(f"    ✅ {inserted_count} contas migradas...")
                
                except Exception as e:
                    print(f"    ❌ Erro na linha {index}: {e}")
                    continue
            
            # Commit das alterações
            session.commit()
            print(f"✅ {inserted_count} contas DRE N0 migradas com sucesso!")
            
            # Verificar resultado final
            print("\n📊 Verificando dados migrados...")
            all_dre_n0 = session.query(DREStructureN0).order_by(DREStructureN0.order_index).all()
            
            print(f"📋 Total de registros na tabela: {len(all_dre_n0)}")
            print("\nEstrutura migrada:")
            for item in all_dre_n0:
                print(f"  {item.dre_n0_id}: {item.name} ({item.operation_type}) - Ordem: {item.order_index}")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Erro durante migração: {e}")
            return False
        finally:
            session.close()
    
    except Exception as e:
        print(f"❌ Erro ao migrar estrutura DRE N0: {e}")
        return False

def validate_migration():
    """Validar a migração comparando com o Excel"""
    print("\n🔍 VALIDANDO MIGRAÇÃO DRE N0")
    print("=" * 40)
    
    try:
        # Carregar dados do Excel
        filename = "db_bluefit - Copia.xlsx"
        df_excel = pd.read_excel(filename, sheet_name="dre")
        
        # Buscar dados do PostgreSQL
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        db_data = session.query(DREStructureN0).all()
        
        print(f"📊 Excel: {len(df_excel)} registros")
        print(f"📊 PostgreSQL: {len(db_data)} registros")
        
        if len(df_excel) == len(db_data):
            print("✅ Contagem de registros confere!")
        else:
            print("⚠️  Diferença na contagem de registros")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")

def main():
    """Função principal"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            success = migrate_dre_n0_structure()
            if success:
                print("\n🎉 Migração DRE N0 concluída com sucesso!")
            else:
                print("\n❌ Migração DRE N0 falhou!")
        elif command == "validate":
            validate_migration()
        else:
            print("Comandos disponíveis: migrate, validate")
    else:
        print("🚀 MIGRAÇÃO DA ESTRUTURA DRE N0")
        print("=" * 40)
        print("Comandos disponíveis:")
        print("  python3 migrate_dre_n0_structure.py migrate  - Executar migração")
        print("  python3 migrate_dre_n0_structure.py validate - Validar migração")

if __name__ == "__main__":
    main()
