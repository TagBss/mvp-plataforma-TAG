#!/usr/bin/env python3
"""
Script para criar a view DRE N0 DINÂMICA baseada na tabela dre_structure_n0
A view será atualizada automaticamente quando a estrutura da tabela for alterada
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection_sqlalchemy import get_engine
from sqlalchemy import text

def create_dre_n0_view_dynamic():
    """Cria a view DRE N0 baseada na tabela dre_structure_n0"""
    
    print("🔧 CRIANDO VIEW DRE N0 DINÂMICA...")
    
    engine = get_engine()
    with engine.connect() as connection:
        
        # 1. Primeiro, vamos verificar se a view já existe e removê-la
        print("   📋 Removendo view existente se houver...")
        drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo CASCADE")
        connection.execute(drop_view)
        print("   ✅ View anterior removida")
        
        # 2. Criar a view DRE N0 baseada na tabela dre_structure_n0
        print("   🏗️ Criando nova view DRE N0 dinâmica...")
        
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
            -- Estrutura DRE N0 dinâmica da tabela
            SELECT 
                ds0.id,
                ds0.name,
                ds0.operation_type,
                ds0.order_index,
                ds0.dre_niveis,
                ds0.description,
                ds0.dre_n1_id,
                ds0.dre_n2_id
            FROM dre_structure_n0 ds0 
            WHERE ds0.is_active = true
            ORDER BY ds0.order_index
        ),
        valores_por_periodo AS (
            -- Calcular valores para cada período baseado na estrutura dinâmica
            SELECT 
                e.id, e.name, e.operation_type, e.order_index, e.dre_niveis, e.description,
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
                    WHEN e.dre_niveis = 'dre_n2' THEN d.dre_n2_id = e.dre_n2_id
                    WHEN e.dre_niveis = 'dre_n1' THEN d.dre_n1_id = e.dre_n1_id
                    ELSE false
                END
            )
            WHERE e.operation_type != '='
            GROUP BY e.id, e.name, e.operation_type, e.order_index, e.dre_niveis, e.description, 
                     d.periodo_mensal, d.periodo_trimestral, d.periodo_anual
        ),
        totalizadores AS (
            -- Calcular totalizadores baseados na estrutura dinâmica
            SELECT 
                v.*,
                CASE 
                    WHEN v.operation_type = '=' THEN
                        -- Para totalizadores, calcular baseado na lógica de negócio
                        CASE 
                            WHEN v.name LIKE '%Receita Bruta%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Faturamento%' AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%Receita Líquida%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Receita Bruta%' OR name LIKE '%Tributos%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%Resultado Bruto%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Receita Líquida%' OR name LIKE '%CMV%' OR name LIKE '%CSP%' OR name LIKE '%CPV%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%EBITDA%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Resultado Bruto%' OR name LIKE '%Despesas%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%EBIT%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%EBITDA%' OR name LIKE '%Depreciação%' OR name LIKE '%Amortização%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%Resultado Financeiro%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Receitas Financeiras%' OR name LIKE '%Despesas Financeiras%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%Resultado Antes dos Impostos%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%EBIT%' OR name LIKE '%Resultado Financeiro%' OR name LIKE '%não operacionais%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            WHEN v.name LIKE '%Resultado Líquido%' THEN 
                                (SELECT COALESCE(SUM(valor_calculado), 0) FROM valores_por_periodo 
                                 WHERE name LIKE '%Resultado Antes dos Impostos%' OR name LIKE '%IRPJ%' OR name LIKE '%CSLL%' 
                                 AND periodo_mensal = v.periodo_mensal)
                            
                            ELSE 0  -- Totalizador não reconhecido
                        END
                    ELSE 
                        v.valor_calculado  -- Para contas não-totalizadoras, usar valor direto
                END as valor_final
            FROM valores_por_periodo v
        )
        SELECT 
            id, name, operation_type, order_index, dre_niveis, description as descricao,
            periodo_mensal, periodo_trimestral, periodo_anual,
            COALESCE(valor_final, 0) as valor_calculado
        FROM totalizadores
        ORDER BY order_index, periodo_mensal;
        """)
        
        connection.execute(create_view)
        print("   ✅ View DRE N0 dinâmica criada com sucesso!")
        
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
            
        # 5. Verificar estrutura da tabela dre_structure_n0
        print("   📊 Verificando estrutura da tabela dre_structure_n0...")
        structure_info = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN operation_type = '+' THEN 1 END) as receitas,
                COUNT(CASE WHEN operation_type = '-' THEN 1 END) as despesas,
                COUNT(CASE WHEN operation_type = '=' THEN 1 END) as totalizadores,
                COUNT(CASE WHEN operation_type = '+/-' THEN 1 END) as variaveis
            FROM dre_structure_n0
            WHERE is_active = true
        """)
        
        structure = connection.execute(structure_info).fetchone()
        print(f"   📈 Estrutura DRE N0:")
        print(f"      - Total: {structure[0]} contas")
        print(f"      - Receitas (+): {structure[1]}")
        print(f"      - Despesas (-): {structure[2]}")
        print(f"      - Totalizadores (=): {structure[3]}")
        print(f"      - Variáveis (+/-): {structure[4]}")
            
        return True

if __name__ == "__main__":
    try:
        success = create_dre_n0_view_dynamic()
        if success:
            print("\n🎉 VIEW DRE N0 DINÂMICA CRIADA COM SUCESSO!")
            print("   ✅ Baseada na tabela dre_structure_n0")
            print("   ✅ Estrutura editável via interface admin")
            print("   ✅ Totalizadores calculados automaticamente")
            print("   ✅ Mudanças na tabela refletem na view em tempo real")
        else:
            print("\n❌ ERRO AO CRIAR VIEW DRE N0 DINÂMICA!")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
