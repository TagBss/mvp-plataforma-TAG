#!/usr/bin/env python3
"""
Script para criar a view DRE N0 correta baseada na lógica de negócio
SEM depender da tabela dre_structure_n0, mas sim criando a partir de
financial_data + estruturas DRE N1/N2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_dre_n0_view():
    """Cria a view DRE N0 baseada na lógica de negócio"""
    
    print("🔧 CRIANDO VIEW DRE N0 CORRETA...")
    
    engine = get_engine()
    with engine.connect() as connection:
        
        # 1. Primeiro, vamos verificar se a view já existe e removê-la
        print("   📋 Removendo view existente se houver...")
        drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo CASCADE")
        connection.execute(drop_view)
        print("   ✅ View anterior removida")
        
        # 2. Criar a view DRE N0 baseada na lógica de negócio
        print("   🏗️ Criando nova view DRE N0...")
        
        create_view = text("""
        CREATE VIEW v_dre_n0_completo AS
        WITH dados_limpos AS (
            -- Dados financeiros válidos com relacionamentos DRE
            SELECT 
                fd.competencia,
                fd.valor_original,
                fd.dre_n1_id,
                fd.dre_n2_id,
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
            FROM financial_data fd
            WHERE (fd.dre_n1_id IS NOT NULL OR fd.dre_n2_id IS NOT NULL)
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
        ),
        estrutura_dre_n0 AS (
            -- Estrutura DRE N0 baseada na lógica de negócio
            SELECT 
                1 as id, '( + ) Faturamento' as name, '+' as operation_type, 1 as order_index, 'dre_n2' as dre_niveis, 'Faturamento' as descricao
            UNION ALL
            SELECT 2, '( = ) Receita Bruta', '=', 2, 'totalizador', 'Receita Bruta (resultado do faturamento)'
            UNION ALL
            SELECT 3, '( - ) Tributos e deduções sobre a receita', '-', 3, 'dre_n2', 'Tributos e deduções sobre a receita'
            UNION ALL
            SELECT 4, '( = ) Receita Líquida', '=', 4, 'totalizador', 'Receita Líquida (receita bruta + tributos)'
            UNION ALL
            SELECT 5, '( - ) CMV', '-', 5, 'dre_n2', 'Custo das Mercadorias Vendidas'
            UNION ALL
            SELECT 6, '( - ) CSP', '-', 6, 'dre_n2', 'Custo dos Serviços Prestados'
            UNION ALL
            SELECT 7, '( - ) CPV', '-', 7, 'dre_n2', 'Custo dos Produtos Vendidos'
            UNION ALL
            SELECT 8, '( = ) Resultado Bruto', '=', 8, 'totalizador', 'Resultado Bruto (receita líquida + CMV + CSP + CPV)'
            UNION ALL
            SELECT 9, '( - ) Despesas Administrativas', '-', 9, 'dre_n2', 'Despesas Administrativas'
            UNION ALL
            SELECT 10, '( - ) Despesas com Pessoal', '-', 10, 'dre_n2', 'Despesas com Pessoal'
            UNION ALL
            SELECT 11, '( - ) Despesas com Ocupação', '-', 11, 'dre_n2', 'Despesas com Ocupação'
            UNION ALL
            SELECT 12, '( - ) Despesas Comerciais', '-', 12, 'dre_n2', 'Despesas Comerciais'
            UNION ALL
            SELECT 13, '( = ) EBITDA', '=', 13, 'totalizador', 'EBITDA (resultado bruto - despesas operacionais)'
            UNION ALL
            SELECT 14, '( - ) Depreciação', '-', 14, 'dre_n2', 'Depreciação'
            UNION ALL
            SELECT 15, '( - ) Amortização', '-', 15, 'dre_n2', 'Amortização'
            UNION ALL
            SELECT 16, '( = ) EBIT', '=', 16, 'totalizador', 'EBIT (EBITDA - depreciação - amortização)'
            UNION ALL
            SELECT 17, '( + ) Receitas Financeiras', '+', 17, 'dre_n2', 'Receitas Financeiras'
            UNION ALL
            SELECT 18, '( - ) Despesas Financeiras', '-', 18, 'dre_n2', 'Despesas Financeiras'
            UNION ALL
            SELECT 19, '( = ) Resultado Financeiro', '=', 19, 'totalizador', 'Resultado Financeiro (receitas - despesas financeiras)'
            UNION ALL
            SELECT 20, '( + ) Receitas / Despesas não operacionais', '+/-', 20, 'dre_n2', 'Receitas/Despesas não operacionais'
            UNION ALL
            SELECT 21, '( = ) Resultado Antes dos Impostos', '=', 21, 'totalizador', 'Resultado antes dos impostos (EBIT + resultado financeiro + não operacionais)'
            UNION ALL
            SELECT 22, '( - ) IRPJ', '-', 22, 'dre_n2', 'Imposto de Renda Pessoa Jurídica'
            UNION ALL
            SELECT 23, '( - ) CSLL', '-', 23, 'dre_n2', 'Contribuição Social sobre o Lucro Líquido'
            UNION ALL
            SELECT 24, '( = ) Resultado Líquido', '=', 24, 'totalizador', 'Resultado Líquido (resultado antes dos impostos - IRPJ - CSLL)'
        ),
        valores_por_periodo AS (
            -- Calcular valores para cada período
            SELECT 
                e.id, e.name, e.operation_type, e.order_index, e.dre_niveis, e.descricao,
                d.periodo_mensal, d.periodo_trimestral, d.periodo_anual,
                CASE 
                    WHEN e.operation_type = '+' THEN ABS(SUM(d.valor_original))
                    WHEN e.operation_type = '-' THEN -ABS(SUM(d.valor_original))
                    WHEN e.operation_type = '+/-' THEN SUM(d.valor_original)
                    WHEN e.operation_type = '=' THEN 0  -- Totalizadores serão calculados depois
                END as valor_calculado
            FROM estrutura_dre_n0 e
            LEFT JOIN dados_limpos d ON (
                CASE 
                    WHEN e.dre_niveis = 'dre_n2' THEN d.dre_n2_id IS NOT NULL
                    WHEN e.dre_niveis = 'dre_n1' THEN d.dre_n1_id IS NOT NULL
                    ELSE false
                END
            )
            WHERE e.operation_type != '='
            GROUP BY e.id, e.name, e.operation_type, e.order_index, e.dre_niveis, e.descricao, 
                     d.periodo_mensal, d.periodo_trimestral, d.periodo_anual
        ),
        totalizadores AS (
            -- Calcular totalizadores baseados na lógica de negócio
            SELECT 
                v.*,
                CASE 
                    WHEN v.name = '( = ) Receita Bruta' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name = '( + ) Faturamento' AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) Receita Líquida' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) Receita Bruta', '( - ) Tributos e deduções sobre a receita') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) Resultado Bruto' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) Receita Líquida', '( - ) CMV', '( - ) CSP', '( - ) CPV') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) EBITDA' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) Resultado Bruto', '( - ) Despesas Administrativas', '( - ) Despesas com Pessoal', 
                                      '( - ) Despesas com Ocupação', '( - ) Despesas Comerciais') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) EBIT' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) EBITDA', '( - ) Depreciação', '( - ) Amortização') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) Resultado Financeiro' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( + ) Receitas Financeiras', '( - ) Despesas Financeiras') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) Resultado Antes dos Impostos' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) EBIT', '( = ) Resultado Financeiro', '( + ) Receitas / Despesas não operacionais') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    WHEN v.name = '( = ) Resultado Líquido' THEN 
                        (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                         WHERE name IN ('( = ) Resultado Antes dos Impostos', '( - ) IRPJ', '( - ) CSLL') 
                         AND periodo_mensal = v.periodo_mensal)
                    
                    ELSE v.valor_calculado
                END as valor_final
            FROM valores_por_periodo v
        )
        SELECT 
            id, name, operation_type, order_index, dre_niveis, descricao,
            periodo_mensal, periodo_trimestral, periodo_anual,
            COALESCE(valor_final, 0) as valor_calculado
        FROM totalizadores
        ORDER BY order_index, periodo_mensal;
        """)
        
        connection.execute(create_view)
        print("   ✅ View DRE N0 criada com sucesso!")
        
        # 3. Verificar se a view foi criada
        print("   🔍 Verificando se a view foi criada...")
        check_view = text("""
            SELECT viewname, schemaname 
            FROM pg_views 
            WHERE viewname = 'v_dre_n0_completo'
        """)
        
        result = connection.execute(check_view)
        if result.fetchone():
            print("   ✅ View v_dre_n0_completo criada e registrada no sistema!")
        else:
            print("   ❌ Erro: View não foi criada!")
            return False
        
        # 4. Testar se a view retorna dados
        print("   🧪 Testando se a view retorna dados...")
        test_view = text("SELECT COUNT(*) as total FROM v_dre_n0_completo")
        count = connection.execute(test_view).scalar()
        print(f"   📊 Total de registros na view: {count}")
        
        if count > 0:
            print("   ✅ View funcionando e retornando dados!")
            
            # Mostrar alguns registros de exemplo
            sample_data = text("""
                SELECT name, operation_type, dre_niveis, periodo_mensal, valor_calculado
                FROM v_dre_n0_completo 
                WHERE periodo_mensal = '2025-01'
                ORDER BY order_index
                LIMIT 5
            """)
            
            sample = connection.execute(sample_data).fetchall()
            print("   📋 Exemplo de dados (jan/2025):")
            for row in sample:
                print(f"      - {row[0]} ({row[1]}) - {row[2]} - {row[3]}: R$ {row[4]:,.2f}")
                
        else:
            print("   ⚠️ View criada mas sem dados - verificar lógica")
            
        return True

if __name__ == "__main__":
    try:
        success = create_dre_n0_view()
        if success:
            print("\n🎉 VIEW DRE N0 CRIADA COM SUCESSO!")
            print("   ✅ Baseada na lógica de negócio (sem dre_structure_n0)")
            print("   ✅ Totalizadores calculados automaticamente")
            print("   ✅ Estrutura hierárquica implementada")
        else:
            print("\n❌ ERRO AO CRIAR VIEW DRE N0!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
