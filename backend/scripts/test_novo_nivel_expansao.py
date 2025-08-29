#!/usr/bin/env python3
"""
Script de teste para o novo nível de expansão por nome na estrutura DRE
Testa a hierarquia: Classificação > Nome > Valores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from helpers_postgresql.dre.classificacoes_helper import ClassificacoesHelper

def test_novo_nivel_expansao():
    """Testa o novo nível de expansão por nome"""
    
    print("🧪 TESTE DO NOVO NÍVEL DE EXPANSÃO POR NOME")
    print("=" * 60)
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            print("✅ Conexão com banco estabelecida")
            
            # Teste 1: Buscar classificações para Faturamento
            print("\n🔍 TESTE 1: Buscar classificações para Faturamento")
            print("-" * 40)
            
            classificacoes = ClassificacoesHelper.fetch_classificacoes_data(
                connection, 
                "Faturamento", 
                None  # Todas as empresas
            )
            
            print(f"📊 Classificações encontradas: {len(classificacoes)}")
            
            if classificacoes:
                # Pegar a primeira classificação para teste
                primeira_classificacao = classificacoes[0].classificacao
                print(f"🎯 Testando com classificação: {primeira_classificacao}")
                
                # Teste 2: Buscar nomes para essa classificação
                print(f"\n🔍 TESTE 2: Buscar nomes para classificação '{primeira_classificacao}'")
                print("-" * 60)
                
                nomes = ClassificacoesHelper.fetch_nomes_por_classificacao(
                    connection,
                    "Faturamento",
                    primeira_classificacao,
                    None  # Todas as empresas
                )
                
                print(f"📊 Nomes encontrados: {len(nomes)}")
                
                if nomes:
                    print("\n📋 Primeiros 5 nomes encontrados:")
                    for i, nome in enumerate(nomes[:5]):
                        print(f"  {i+1}. {nome.nome_lancamento} - R$ {nome.valor_original:.2f} ({nome.periodo_mensal})")
                    
                    # Teste 3: Processar nomes
                    print(f"\n🔍 TESTE 3: Processar nomes para classificação '{primeira_classificacao}'")
                    print("-" * 60)
                    
                    nomes_processados, meses, trimestres, anos = ClassificacoesHelper.process_nomes_por_classificacao(
                        nomes, 
                        []  # Sem dados de faturamento para este teste
                    )
                    
                    print(f"📊 Nomes processados: {len(nomes_processados)}")
                    print(f"📅 Meses: {sorted(list(meses))}")
                    print(f"📅 Trimestres: {sorted(list(trimestres))}")
                    print(f"📅 Anos: {sorted(list(anos))}")
                    
                    if nomes_processados:
                        print(f"\n📋 Primeiro nome processado:")
                        primeiro_nome = nomes_processados[0]
                        print(f"  Nome: {primeiro_nome['nome_lancamento']}")
                        print(f"  Valor Total: R$ {primeiro_nome['valor_total']:.2f}")
                        print(f"  Total Lançamentos: {primeiro_nome['total_lancamentos']}")
                        print(f"  Valores Mensais: {len(primeiro_nome['valores_mensais'])} períodos")
                        print(f"  Valores Trimestrais: {len(primeiro_nome['valores_trimestrais'])} períodos")
                        print(f"  Valores Anuais: {len(primeiro_nome['valores_anuais'])} períodos")
                        
                        # Mostrar alguns valores mensais
                        if primeiro_nome['valores_mensais']:
                            print(f"  Exemplo valores mensais:")
                            for periodo, valor in list(primeiro_nome['valores_mensais'].items())[:3]:
                                print(f"    {periodo}: R$ {valor:.2f}")
                else:
                    print("❌ Nenhum nome encontrado para a classificação")
            else:
                print("❌ Nenhuma classificação encontrada para Faturamento")
            
            # Teste 4: Verificar estrutura da tabela financial_data
            print(f"\n🔍 TESTE 4: Verificar estrutura da tabela financial_data")
            print("-" * 50)
            
            estrutura_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'financial_data'
                AND column_name IN ('nome', 'classificacao', 'valor_original', 'competencia')
                ORDER BY column_name
            """)
            
            result = connection.execute(estrutura_query)
            colunas = result.fetchall()
            
            print("📋 Colunas relevantes da tabela financial_data:")
            for col in colunas:
                print(f"  {col.column_name}: {col.data_type} (nullable: {col.is_nullable})")
            
            # Teste 5: Verificar dados de exemplo
            print(f"\n🔍 TESTE 5: Verificar dados de exemplo")
            print("-" * 40)
            
            dados_query = text("""
                SELECT nome, classificacao, valor_original, competencia
                FROM financial_data
                WHERE nome IS NOT NULL 
                AND nome::text <> ''
                AND nome::text <> 'nan'
                AND classificacao IS NOT NULL
                AND valor_original IS NOT NULL
                LIMIT 5
            """)
            
            result = connection.execute(dados_query)
            dados = result.fetchall()
            
            print(f"📊 Dados de exemplo encontrados: {len(dados)}")
            for i, dado in enumerate(dados):
                print(f"  {i+1}. Nome: {dado.nome}")
                print(f"     Classificação: {dado.classificacao}")
                print(f"     Valor: R$ {dado.valor_original:.2f}")
                print(f"     Competência: {dado.competencia}")
                print()
            
            print("✅ Todos os testes concluídos com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()

def test_endpoint_nomes():
    """Testa o endpoint de nomes via HTTP"""
    
    print("\n🌐 TESTE DO ENDPOINT DE NOMES VIA HTTP")
    print("=" * 50)
    
    try:
        import requests
        
        # Testar endpoint de classificações primeiro
        print("🔍 Testando endpoint de classificações...")
        response = requests.get("http://localhost:8000/dre-n0/classificacoes/Faturamento")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Classificações retornadas: {data.get('total_classificacoes', 0)}")
            
            if data.get('data'):
                primeira_classificacao = data['data'][0]['classificacao']
                print(f"🎯 Testando com classificação: {primeira_classificacao}")
                
                # Testar endpoint de nomes
                print(f"🔍 Testando endpoint de nomes...")
                nome_url = f"http://localhost:8000/dre-n0/classificacoes/Faturamento/nomes/{primeira_classificacao}"
                print(f"URL: {nome_url}")
                
                response_nomes = requests.get(nome_url)
                
                if response_nomes.status_code == 200:
                    data_nomes = response_nomes.json()
                    print(f"✅ Nomes retornados: {data_nomes.get('total_nomes', 0)}")
                    print(f"📅 Meses: {data_nomes.get('meses', [])}")
                    print(f"📅 Trimestres: {data_nomes.get('trimestres', [])}")
                    print(f"📅 Anos: {data_nomes.get('anos', [])}")
                    
                    if data_nomes.get('data'):
                        print(f"\n📋 Primeiros nomes:")
                        for i, nome in enumerate(data_nomes['data'][:3]):
                            print(f"  {i+1}. {nome['nome_lancamento']} - R$ {nome['valor_total']:.2f}")
                else:
                    print(f"❌ Erro no endpoint de nomes: {response_nomes.status_code}")
                    print(f"Resposta: {response_nomes.text}")
            else:
                print("❌ Nenhuma classificação retornada")
        else:
            print(f"❌ Erro no endpoint de classificações: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except ImportError:
        print("⚠️ requests não disponível - pulando teste HTTP")
    except Exception as e:
        print(f"❌ Erro no teste HTTP: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando testes do novo nível de expansão por nome")
    print("=" * 70)
    
    # Teste direto no banco
    test_novo_nivel_expansao()
    
    # Teste via HTTP (se disponível)
    test_endpoint_nomes()
    
    print("\n🎉 Testes concluídos!")
    print("=" * 70)
