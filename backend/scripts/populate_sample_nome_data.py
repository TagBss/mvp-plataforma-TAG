#!/usr/bin/env python3
"""
Script para popular dados de exemplo na tabela financial_data
para testar o novo nível de expansão por nome
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text
from datetime import date, timedelta
import random

def populate_sample_nome_data():
    """Popula dados de exemplo para testar o novo nível de expansão por nome"""
    
    print("🚀 POPULANDO DADOS DE EXEMPLO PARA NOVO NÍVEL DE EXPANSÃO")
    print("=" * 70)
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            print("✅ Conexão com banco estabelecida")
            
            # Verificar se já existem dados
            check_query = text("""
                SELECT COUNT(*) as total
                FROM financial_data
                WHERE nome IS NOT NULL 
                AND nome::text <> ''
                AND nome::text <> 'nan'
                AND nome LIKE 'Exemplo%'
            """)
            
            result = connection.execute(check_query)
            existing_count = result.fetchone().total
            
            if existing_count > 0:
                print(f"⚠️ Já existem {existing_count} registros de exemplo. Removendo...")
                
                delete_query = text("""
                    DELETE FROM financial_data
                    WHERE nome LIKE 'Exemplo%'
                """)
                
                connection.execute(delete_query)
                connection.commit()
                print("✅ Registros de exemplo removidos")
            
            # Verificar empresas disponíveis
            empresas_query = text("SELECT id, nome FROM empresas LIMIT 5")
            result = connection.execute(empresas_query)
            empresas = result.fetchall()
            
            if not empresas:
                print("❌ Nenhuma empresa encontrada. Criando empresa de exemplo...")
                
                # Criar empresa de exemplo
                create_empresa_query = text("""
                    INSERT INTO empresas (id, nome, is_active, created_at, updated_at)
                    VALUES (uuid_generate_v4(), 'Empresa Teste', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """)
                
                result = connection.execute(create_empresa_query)
                empresa_id = result.fetchone().id
                connection.commit()
                print(f"✅ Empresa de exemplo criada: {empresa_id}")
            else:
                empresa_id = empresas[0].id
                print(f"✅ Usando empresa existente: {empresas[0].nome} ({empresa_id})")
            
            # Verificar classificações disponíveis
            classificacoes_query = text("""
                SELECT DISTINCT classificacao
                FROM financial_data
                WHERE classificacao IS NOT NULL 
                AND classificacao::text <> ''
                AND classificacao::text <> 'nan'
                LIMIT 10
            """)
            
            result = connection.execute(classificacoes_query)
            classificacoes = [row.classificacao for row in result.fetchall()]
            
            if not classificacoes:
                print("❌ Nenhuma classificação encontrada. Criando classificações de exemplo...")
                classificacoes = [
                    "Exemplo Receita 1",
                    "Exemplo Receita 2", 
                    "Exemplo Despesa 1",
                    "Exemplo Despesa 2"
                ]
            
            print(f"✅ Usando {len(classificacoes)} classificações existentes")
            
            # Dados de exemplo para nomes
            nomes_exemplo = [
                "Exemplo Lançamento A",
                "Exemplo Lançamento B",
                "Exemplo Lançamento C",
                "Exemplo Lançamento D",
                "Exemplo Lançamento E",
                "Exemplo Lançamento F",
                "Exemplo Lançamento G",
                "Exemplo Lançamento H"
            ]
            
            # Períodos de exemplo (últimos 12 meses)
            data_base = date.today()
            periodos = []
            for i in range(12):
                data = data_base - timedelta(days=30*i)
                periodos.append(data)
            
            print(f"✅ Criando {len(nomes_exemplo)} nomes de exemplo para {len(periodos)} períodos")
            
            # Inserir dados de exemplo
            registros_criados = 0
            
            for nome in nomes_exemplo:
                for periodo in periodos:
                    for classificacao in random.sample(classificacoes, random.randint(1, 3)):
                        
                        # Valor aleatório entre 100 e 10000
                        valor = round(random.uniform(100, 10000), 2)
                        
                        # 50% chance de ser negativo (despesa)
                        if random.random() > 0.5:
                            valor = -valor
                        
                        insert_query = text("""
                            INSERT INTO financial_data (
                                id, origem, empresa, nome, classificacao, competencia, 
                                valor_original, data, valor, empresa_id,
                                created_at, updated_at
                            ) VALUES (
                                uuid_generate_v4(), :origem, :empresa, :nome, :classificacao, :competencia,
                                :valor_original, :data, :valor, :empresa_id,
                                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            )
                        """)
                        
                        params = {
                            "origem": "EXEMPLO",
                            "empresa": "Empresa Teste",
                            "nome": nome,
                            "classificacao": classificacao,
                            "competencia": periodo,
                            "valor_original": valor,
                            "data": periodo,
                            "valor": valor,
                            "empresa_id": empresa_id
                        }
                        
                        connection.execute(insert_query, params)
                        registros_criados += 1
            
            connection.commit()
            print(f"✅ {registros_criados} registros de exemplo criados com sucesso!")
            
            # Verificar dados criados
            verify_query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT nome) as nomes_unicos,
                    COUNT(DISTINCT classificacao) as classificacoes_unicas,
                    COUNT(DISTINCT competencia) as periodos_unicos
                FROM financial_data
                WHERE nome LIKE 'Exemplo%'
            """)
            
            result = connection.execute(verify_query)
            stats = result.fetchone()
            
            print(f"\n📊 ESTATÍSTICAS DOS DADOS CRIADOS:")
            print(f"  Total de registros: {stats.total}")
            print(f"  Nomes únicos: {stats.nomes_unicos}")
            print(f"  Classificações únicas: {stats.classificacoes_unicas}")
            print(f"  Períodos únicos: {stats.periodos_unicos}")
            
            # Mostrar alguns exemplos
            sample_query = text("""
                SELECT nome, classificacao, valor_original, competencia
                FROM financial_data
                WHERE nome LIKE 'Exemplo%'
                ORDER BY nome, competencia
                LIMIT 10
            """)
            
            result = connection.execute(sample_query)
            exemplos = result.fetchall()
            
            print(f"\n📋 EXEMPLOS DE DADOS CRIADOS:")
            for i, exemplo in enumerate(exemplos):
                print(f"  {i+1}. {exemplo.nome} - {exemplo.classificacao}")
                print(f"     R$ {exemplo.valor_original:.2f} ({exemplo.competencia})")
            
            print("\n✅ Dados de exemplo populados com sucesso!")
            print("🎯 Agora você pode testar o novo nível de expansão por nome!")
            
    except Exception as e:
        print(f"❌ Erro ao popular dados de exemplo: {str(e)}")
        import traceback
        traceback.print_exc()

def cleanup_sample_data():
    """Remove dados de exemplo criados para teste"""
    
    print("🧹 REMOVENDO DADOS DE EXEMPLO")
    print("=" * 40)
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            print("✅ Conexão com banco estabelecida")
            
            # Contar registros antes da remoção
            count_before_query = text("""
                SELECT COUNT(*) as total
                FROM financial_data
                WHERE nome LIKE 'Exemplo%'
            """)
            
            result = connection.execute(count_before_query)
            count_before = result.fetchone().total
            
            if count_before == 0:
                print("✅ Nenhum dado de exemplo encontrado para remover")
                return
            
            print(f"📊 Encontrados {count_before} registros de exemplo")
            
            # Remover dados de exemplo
            delete_query = text("""
                DELETE FROM financial_data
                WHERE nome LIKE 'Exemplo%'
            """)
            
            connection.execute(delete_query)
            connection.commit()
            
            print(f"✅ {count_before} registros de exemplo removidos com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro ao remover dados de exemplo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script para popular dados de exemplo para teste do novo nível de expansão")
    parser.add_argument("--cleanup", action="store_true", help="Remove dados de exemplo em vez de criar")
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_sample_data()
    else:
        populate_sample_nome_data()
        
        print("\n" + "="*70)
        print("🚀 PRÓXIMOS PASSOS:")
        print("1. Execute o script de teste: python scripts/test_novo_nivel_expansao.py")
        print("2. Teste o endpoint: GET /dre-n0/classificacoes/Faturamento/nomes/{nome_classificacao}")
        print("3. Para limpar dados de exemplo: python scripts/populate_sample_nome_data.py --cleanup")
        print("="*70)
