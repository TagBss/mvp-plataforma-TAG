"""
Script para migrar estrutura da Bluefit (abas 'de_para' e 'plano_de_contas')
"""
import pandas as pd
import uuid
from datetime import datetime
from typing import Dict, Any, List
from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import (
    GrupoEmpresa, Empresa, Categoria, PlanoDeContas, DePara
)

def generate_uuid() -> str:
    """Gera UUID único para identificação"""
    return str(uuid.uuid4())

def setup_bluefit_structure():
    """Configura estrutura base da Bluefit no banco"""
    
    print("🏢 Configurando estrutura base da Bluefit...")
    
    with DatabaseSession() as session:
        try:
            # 1. Criar Empresa Bluefit primeiro
            empresa_bluefit = session.query(Empresa).filter(
                Empresa.nome == "Bluefit"
            ).first()
            
            if not empresa_bluefit:
                empresa_bluefit = Empresa(
                    id=generate_uuid(),
                    nome="Bluefit",
                    is_active=True
                )
                session.add(empresa_bluefit)
                session.flush()
                print(f"✅ Empresa criada: {empresa_bluefit.nome} (ID: {empresa_bluefit.id})")
            else:
                print(f"✅ Empresa já existe: {empresa_bluefit.nome}")
            
            # 2. Criar Grupo Empresa vinculado à empresa Bluefit
            grupo_bluefit = session.query(GrupoEmpresa).filter(
                GrupoEmpresa.nome == "Bluefit T8"
            ).first()
            
            if not grupo_bluefit:
                grupo_bluefit = GrupoEmpresa(
                    id=generate_uuid(),
                    nome="Bluefit T8",
                    empresa_id=empresa_bluefit.id,
                    is_active=True
                )
                session.add(grupo_bluefit)
                session.flush()
                print(f"✅ Grupo empresa criado: {grupo_bluefit.nome} (ID: {grupo_bluefit.id}) vinculado à empresa {empresa_bluefit.nome}")
            else:
                # Atualizar empresa_id se necessário
                if grupo_bluefit.empresa_id != empresa_bluefit.id:
                    grupo_bluefit.empresa_id = empresa_bluefit.id
                    session.flush()
                    print(f"✅ Grupo empresa {grupo_bluefit.nome} atualizado com empresa {empresa_bluefit.nome}")
                else:
                    print(f"✅ Grupo empresa já existe: {grupo_bluefit.id}")
            
            # 3. Criar categorias básicas
            categorias_basicas = [
                {"nome": "Cliente"},
                {"nome": "Fornecedor"},
                {"nome": "Funcionário"},
                {"nome": "Parceiro"},
            ]
            
            for cat_data in categorias_basicas:
                categoria_existente = session.query(Categoria).filter(
                    Categoria.nome == cat_data["nome"],
                    Categoria.grupo_empresa_id == grupo_bluefit.id
                ).first()
                
                if not categoria_existente:
                    categoria = Categoria(
                        id=generate_uuid(),
                        nome=cat_data["nome"],
                        grupo_empresa_id=grupo_bluefit.id,
                        is_active=True
                    )
                    session.add(categoria)
                    print(f"✅ Categoria criada: {categoria.nome}")
            
            session.commit()
            print("✅ Estrutura base da Bluefit configurada com sucesso!")
            
            return {
                "grupo_empresa_id": grupo_bluefit.id,
                "empresa_id": empresa_bluefit.id
            }
            
        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao configurar estrutura: {e}")
            raise

def migrate_plano_de_contas(excel_file: str = "db_bluefit - Copia.xlsx"):
    """Migra aba 'plano_de_contas' do Excel"""
    
    print(f"📊 Migrando plano de contas do arquivo: {excel_file}")
    
    try:
        # Carregar dados do Excel
        df = pd.read_excel(excel_file, sheet_name='plano_de_contas')
        print(f"📈 Dados carregados: {len(df)} linhas")
        
        # Configurar estrutura base
        estrutura = setup_bluefit_structure()
        grupo_empresa_id = estrutura["grupo_empresa_id"]
        
        with DatabaseSession() as session:
            inserted_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Mapear colunas do Excel para o schema
                    plano_conta = PlanoDeContas(
                        grupo_empresa_id=grupo_empresa_id,
                        conta_pai=str(row.get('para [conta]', '')) if pd.notna(row.get('para [conta]')) else None,
                        conta=str(row.get('conta_cod', '')),
                        nome_conta=str(row.get('conta_desc', '')),
                        tipo_conta=None,  # Não disponível no Excel
                        nivel=1,  # Nível padrão
                        ordem=index + 1,  # Ordem sequencial
                        classificacao_dre=str(row.get('dre_n1', '')) if pd.notna(row.get('dre_n1')) else None,
                        classificacao_dre_n2=str(row.get('dre_n2', '')) if pd.notna(row.get('dre_n2')) else None,
                        classificacao_dfc=str(row.get('dfc_n1', '')) if pd.notna(row.get('dfc_n1')) else None,
                        classificacao_dfc_n2=str(row.get('dfc_n2', '')) if pd.notna(row.get('dfc_n2')) else None,
                        centro_custo=None,  # Não disponível no Excel
                        observacoes=f"ID Original: {row.get('conta_id', '')}",
                        is_active=True
                    )
                    
                    session.add(plano_conta)
                    inserted_count += 1
                    
                    if inserted_count % 20 == 0:
                        print(f"✅ Inseridas {inserted_count} linhas...")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ Erro na linha {index}: {e}")
                    continue
            
            session.commit()
            print(f"✅ Migração do plano de contas concluída!")
            print(f"📊 Total inserido: {inserted_count} registros")
            print(f"❌ Erros: {error_count} registros")
            
    except Exception as e:
        print(f"❌ Erro na migração do plano de contas: {e}")
        raise

def migrate_de_para(excel_file: str = "db_bluefit - Copia.xlsx"):
    """Migra aba 'de_para' do Excel"""
    
    print(f"📊 Migrando tabela de_para do arquivo: {excel_file}")
    
    try:
        # Carregar dados do Excel
        df = pd.read_excel(excel_file, sheet_name='de_para')
        print(f"📈 Dados carregados: {len(df)} linhas")
        
        # Configurar estrutura base
        estrutura = setup_bluefit_structure()
        grupo_empresa_id = estrutura["grupo_empresa_id"]
        
        with DatabaseSession() as session:
            inserted_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Mapear colunas do Excel para o schema
                    de_para = DePara(
                        grupo_empresa_id=grupo_empresa_id,
                        origem_sistema="bluefit_excel",
                        descricao_origem=str(row.get('de [classificacao]', '')),
                        descricao_destino=str(row.get('para [conta]', '')),
                        observacoes=f"Migrado da linha {index + 1} do Excel",
                        is_active=True
                    )
                    
                    session.add(de_para)
                    inserted_count += 1
                    
                    if inserted_count % 20 == 0:
                        print(f"✅ Inseridas {inserted_count} linhas...")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ Erro na linha {index}: {e}")
                    continue
            
            session.commit()
            print(f"✅ Migração da tabela de_para concluída!")
            print(f"📊 Total inserido: {inserted_count} registros")
            print(f"❌ Erros: {error_count} registros")
            
    except Exception as e:
        print(f"❌ Erro na migração da tabela de_para: {e}")
        raise

def validate_migration():
    """Valida a migração das novas tabelas"""
    
    print("🔍 Validando migração das novas tabelas...")
    
    with DatabaseSession() as session:
        try:
            # Contar registros
            total_grupos = session.query(GrupoEmpresa).count()
            total_empresas = session.query(Empresa).count()
            total_categorias = session.query(Categoria).count()
            total_plano_contas = session.query(PlanoDeContas).count()
            total_de_para = session.query(DePara).count()
            
            print(f"📊 Grupos empresa: {total_grupos}")
            print(f"📊 Empresas: {total_empresas}")
            print(f"📊 Categorias: {total_categorias}")
            print(f"📊 Plano de contas: {total_plano_contas}")
            print(f"📊 De/Para: {total_de_para}")
            
            # Verificar estrutura
            if total_grupos > 0 and total_empresas > 0:
                print("✅ Estrutura base configurada corretamente")
            else:
                print("⚠️ Estrutura base não configurada")
            
            if total_plano_contas > 0:
                print("✅ Plano de contas migrado com sucesso")
            else:
                print("⚠️ Plano de contas não migrado")
            
            if total_de_para > 0:
                print("✅ Tabela de_para migrada com sucesso")
            else:
                print("⚠️ Tabela de_para não migrada")
                
        except Exception as e:
            print(f"❌ Erro na validação: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_bluefit_structure()
        elif command == "plano_contas":
            migrate_plano_de_contas()
        elif command == "de_para":
            migrate_de_para()
        elif command == "all":
            setup_bluefit_structure()
            migrate_plano_de_contas()
            migrate_de_para()
        elif command == "validate":
            validate_migration()
        else:
            print("Comandos: setup, plano_contas, de_para, all, validate")
    else:
        print("Comandos: setup, plano_contas, de_para, all, validate")
