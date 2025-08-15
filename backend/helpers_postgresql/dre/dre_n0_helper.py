"""
Helper para funções principais do DRE N0
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Connection
from helpers_postgresql.dre.analysis_helper_postgresql import (
    calcular_analise_horizontal_postgresql, 
    calcular_analise_vertical_postgresql,
    calcular_analises_horizontais_movimentacoes_postgresql
)

class DreN0Helper:
    """Helper para operações principais do DRE N0"""
    
    @staticmethod
    def create_dre_n0_view(connection: Connection) -> bool:
        """Cria ou recria a view v_dre_n0_completo"""
        try:
            # Forçar recriação da view
            drop_view = text("DROP VIEW IF EXISTS v_dre_n0_completo")
            connection.execute(drop_view)
            
            # Criar view corrigida com lógica de totalizadores e todos os períodos
            create_view = text("""
                CREATE OR REPLACE VIEW v_dre_n0_completo AS
                WITH dados_limpos AS (
                    -- Filtrar dados válidos da financial_data
                    SELECT 
                        fd.dre_n2,
                        fd.dre_n1,
                        fd.competencia,
                        fd.valor_original,
                        TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                        CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                        EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
                    FROM financial_data fd
                    WHERE fd.dre_n2 IS NOT NULL 
                    AND fd.dre_n2::text <> '' 
                    AND fd.dre_n2::text <> 'nan'
                    AND fd.valor_original IS NOT NULL 
                    AND fd.competencia IS NOT NULL
                ),
                estrutura_n0 AS (
                    SELECT 
                        ds0.id as dre_n0_id,
                        ds0.name as nome_conta,
                        ds0.operation_type as tipo_operacao,
                        ds0.order_index as ordem,
                        CASE 
                            WHEN ds0.description LIKE 'Conta DRE N0: %' 
                            THEN SUBSTRING(ds0.description FROM 15)
                            ELSE ds0.description
                        END as descricao,
                        CASE 
                            WHEN ds0.operation_type = '=' THEN NULL
                            ELSE ds0.name
                        END as nome_para_match
                    FROM dre_structure_n0 ds0
                    WHERE ds0.is_active = true
                ),
                valores_mensais AS (
                    -- Valores mensais agregados
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_mensal,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_mensal
                ),
                valores_trimestrais AS (
                    -- Valores trimestrais agregados (soma dos meses)
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_trimestral,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_trimestral
                ),
                valores_anuais AS (
                    -- Valores anuais agregados (soma dos meses)
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        d.periodo_anual,
                        CASE 
                            WHEN e.tipo_operacao = '+' THEN ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '-' THEN -ABS(SUM(d.valor_original))
                            WHEN e.tipo_operacao = '+/-' THEN SUM(d.valor_original)
                            ELSE 0
                        END as valor_calculado
                    FROM estrutura_n0 e
                    LEFT JOIN dados_limpos d ON (
                        e.nome_para_match IS NOT NULL AND (
                            (d.dre_n1 = e.nome_para_match)
                            OR
                            (d.dre_n2 = e.nome_para_match)
                        )
                    )
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao, d.periodo_anual
                ),
                valores_agregados AS (
                    SELECT 
                        e.dre_n0_id,
                        e.nome_conta,
                        e.tipo_operacao,
                        e.ordem,
                        e.descricao,
                        
                        -- Valores mensais
                        COALESCE(
                            jsonb_object_agg(
                                vm.periodo_mensal,
                                vm.valor_calculado
                            ) FILTER (WHERE vm.periodo_mensal IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_mensais,
                        
                        -- Valores trimestrais
                        COALESCE(
                            jsonb_object_agg(
                                vt.periodo_trimestral,
                                vt.valor_calculado
                            ) FILTER (WHERE vt.periodo_trimestral IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_trimestrais,
                        
                        -- Valores anuais
                        COALESCE(
                            jsonb_object_agg(
                                va.periodo_anual,
                                va.valor_calculado
                            ) FILTER (WHERE va.periodo_anual IS NOT NULL),
                            '{}'::jsonb
                        ) as valores_anuais
                        
                    FROM estrutura_n0 e
                    LEFT JOIN valores_mensais vm ON e.dre_n0_id = vm.dre_n0_id
                    LEFT JOIN valores_trimestrais vt ON e.dre_n0_id = vt.dre_n0_id
                    LEFT JOIN valores_anuais va ON e.dre_n0_id = va.dre_n0_id
                    WHERE e.tipo_operacao != '='
                    GROUP BY e.dre_n0_id, e.nome_conta, e.tipo_operacao, e.ordem, e.descricao
                )
                SELECT 
                    dre_n0_id,
                    nome_conta,
                    tipo_operacao,
                    ordem,
                    descricao,
                    'CAR' as origem,
                    'BLUEFIT' as empresa,
                    valores_mensais,
                    valores_trimestrais,
                    valores_anuais,
                    '{}'::jsonb as orcamentos_mensais,
                    '{}'::jsonb as orcamentos_trimestrais,
                    '{}'::jsonb as orcamentos_anuais,
                    0 as orcamento_total,
                    0 as valor_total,
                    'v_dre_n0_todos_periodos' as source
                    
                FROM valores_agregados
                
                UNION ALL
                
                -- Adicionar contas totalizadoras com valores vazios (serão calculadas no Python)
                SELECT 
                    ds0.id as dre_n0_id,
                    ds0.name as nome_conta,
                    ds0.operation_type as tipo_operacao,
                    ds0.order_index as ordem,
                    CASE 
                        WHEN ds0.description LIKE 'Conta DRE N0: %' 
                        THEN SUBSTRING(ds0.description FROM 15)
                        ELSE ds0.description
                    END as descricao,
                    'CAR' as origem,
                    'BLUEFIT' as empresa,
                    '{}'::jsonb as valores_mensais,
                    '{}'::jsonb as valores_trimestrais,
                    '{}'::jsonb as valores_anuais,
                    '{}'::jsonb as orcamentos_mensais,
                    '{}'::jsonb as orcamentos_trimestrais,
                    '{}'::jsonb as orcamentos_anuais,
                    0 as orcamento_total,
                    0 as valor_total,
                    'v_dre_n0_totalizadores' as source
                FROM dre_structure_n0 ds0
                WHERE ds0.is_active = true AND ds0.operation_type = '='
                
                ORDER BY ordem;
            """)
            
            connection.execute(create_view)
            connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar view DRE N0: {e}")
            return False
    
    @staticmethod
    def check_view_exists(connection: Connection) -> bool:
        """Verifica se a view v_dre_n0_completo existe"""
        check_view = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_views WHERE viewname = 'v_dre_n0_completo'
            )
        """)
        result = connection.execute(check_view)
        return result.scalar()
    
    @staticmethod
    def fetch_dre_n0_data(connection: Connection) -> List[Any]:
        """Busca dados da view DRE N0"""
        query = text("""
            SELECT 
                dre_n0_id,
                nome_conta,
                tipo_operacao,
                ordem,
                descricao,
                origem,
                empresa,
                valores_mensais,
                valores_trimestrais,
                valores_anuais,
                orcamentos_mensais,
                orcamentos_trimestrais,
                orcamentos_anuais,
                orcamento_total,
                valor_total,
                source
            FROM v_dre_n0_completo
            ORDER BY ordem
        """)
        
        result = connection.execute(query)
        return result.fetchall()
    
    @staticmethod
    def process_dre_items(rows: List[Any]) -> Tuple[List[Dict], set, set, set]:
        """Processa dados da DRE para o formato esperado pelo frontend"""
        dre_items = []
        meses = set()
        trimestres = set()
        anos = set()
        
        # Separar valores reais e totalizadores
        valores_reais = []
        totalizadores = []
        
        # Buscar dados de faturamento para cálculo da AV
        faturamento_data = None
        for row in rows:
            if row.ordem == 1 and row.tipo_operacao == '+':  # Faturamento
                faturamento_data = row
                break
        
        for row in rows:
            if row.tipo_operacao == '=':
                totalizadores.append(row)
            else:
                valores_reais.append(row)
        
        # Processar valores reais primeiro
        valores_reais_por_periodo = {}
        valores_reais_por_nome = {}  # Nova estrutura para busca por nome
        
        for row in valores_reais:
            valores_mensais = row.valores_mensais or {}
            valores_trimestrais = row.valores_trimestrais or {}
            valores_anuais = row.valores_anuais or {}
            
            meses.update(valores_mensais.keys())
            trimestres.update(valores_trimestrais.keys())
            anos.update(valores_anuais.keys())
            
            valores_mensais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_mensais.items()}
            valores_trimestrais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_trimestrais.items()}
            valores_anuais_numeros = {k: float(v) if v is not None else 0.0 for k, v in valores_anuais.items()}
            
            # Verificar se a conta tem classificações (é expansível)
            # Por enquanto, assumir que todas as contas são expansíveis
            tem_classificacoes = True
            
            dre_item = DreN0Helper._create_dre_item(
                row, valores_mensais_numeros, valores_trimestrais_numeros, 
                valores_anuais_numeros, tem_classificacoes, faturamento_data
            )
            
            dre_items.append(dre_item)
            
            # Armazenar para cálculo dos totalizadores (por ordem)
            for periodo, valor in valores_mensais_numeros.items():
                if periodo not in valores_reais_por_periodo:
                    valores_reais_por_periodo[periodo] = {}
                valores_reais_por_periodo[periodo][row.ordem] = {
                    'valor': valor,
                    'tipo': row.tipo_operacao,
                    'nome': row.nome_conta
                }
            
            # Armazenar para cálculo dos totalizadores (por nome)
            for periodo, valor in valores_mensais_numeros.items():
                if periodo not in valores_reais_por_nome:
                    valores_reais_por_nome[periodo] = {}
                valores_reais_por_nome[periodo][row.nome_conta] = valor
        
        # Processar totalizadores
        for tot in totalizadores:
            dre_item_tot = DreN0Helper._create_totalizador_item(
                tot, valores_reais_por_periodo, valores_reais_por_nome, meses, trimestres, anos, faturamento_data, dre_items
            )
            dre_items.append(dre_item_tot)
        
        # Ordenar por ordem
        dre_items.sort(key=lambda x: x.get('ordem', 0))
        
        return dre_items, meses, trimestres, anos
    
    @staticmethod
    def _create_dre_item(row: Any, valores_mensais: Dict, valores_trimestrais: Dict, 
                         valores_anuais: Dict, tem_classificacoes: bool, faturamento_data: Any = None) -> Dict:
        """Cria item DRE individual"""
        
        # Usar função já existente para calcular análises horizontais
        meses_ordenados = sorted(valores_mensais.keys())
        trimestres_ordenados = sorted(valores_trimestrais.keys())
        anos_ordenados = sorted(valores_anuais.keys())
        
        # Calcular análises usando funções já existentes
        analises = calcular_analises_horizontais_movimentacoes_postgresql(
            valores_mensais, valores_trimestrais, valores_anuais,
            meses_ordenados, trimestres_ordenados, anos_ordenados
        )
        
        # Calcular análises verticais (baseado no faturamento)
        analise_vertical_mensal = {}
        analise_vertical_trimestral = {}
        analise_vertical_anual = {}
        
        if faturamento_data and faturamento_data.valores_mensais:
            faturamento_mensais = faturamento_data.valores_mensais or {}
            faturamento_trimestrais = faturamento_data.valores_trimestrais or {}
            faturamento_anuais = faturamento_data.valores_anuais or {}
            
            # Para o Faturamento (ordem 1), a AV é sempre 100%
            if row.ordem == 1:
                analise_vertical_mensal = {mes: "100.00%" for mes in valores_mensais.keys()}
                analise_vertical_trimestral = {tri: "100.00%" for tri in valores_trimestrais.keys()}
                analise_vertical_anual = {ano: "100.00%" for ano in valores_anuais.keys()}
            else:
                # Para outras contas, usar função já existente
                for mes in valores_mensais.keys():
                    faturamento_mes = faturamento_mensais.get(mes, 0)
                    analise_vertical_mensal[mes] = calcular_analise_vertical_postgresql(valores_mensais[mes], faturamento_mes)
                
                for tri in valores_trimestrais.keys():
                    faturamento_tri = faturamento_trimestrais.get(tri, 0)
                    analise_vertical_trimestral[tri] = calcular_analise_vertical_postgresql(valores_trimestrais[tri], faturamento_tri)
                
                for ano in valores_anuais.keys():
                    faturamento_ano = faturamento_anuais.get(str(ano), 0)
                    analise_vertical_anual[ano] = calcular_analise_vertical_postgresql(valores_anuais[ano], faturamento_ano)
        else:
            # Fallback se não houver dados de faturamento
            analise_vertical_mensal = {mes: "–" for mes in valores_mensais.keys()}
            analise_vertical_trimestral = {tri: "–" for tri in valores_trimestrais.keys()}
            analise_vertical_anual = {ano: "–" for ano in valores_anuais.keys()}
        
        return {
            "tipo": row.tipo_operacao,
            "nome": row.nome_conta,
            "ordem": row.ordem,
            "expandivel": tem_classificacoes,
            "valores_mensais": valores_mensais,
            "valores_trimestrais": valores_trimestrais,
            "valores_anuais": valores_anuais,
            "orcamentos_mensais": {},
            "orcamentos_trimestrais": {},
            "orcamentos_anuais": {},
            "orcamento_total": 0.0,
            "classificacoes": [],
            # Análise Horizontal e Vertical para contas reais (usando funções já existentes)
            "analise_horizontal_mensal": analises["horizontal_mensais"],
            "analise_vertical_mensal": analise_vertical_mensal,
            "analise_horizontal_trimestral": analises["horizontal_trimestrais"],
            "analise_vertical_trimestral": analise_vertical_trimestral,
            "analise_horizontal_anual": analises["horizontal_anuais"],
            "analise_vertical_anual": analise_vertical_anual
        }
    
    @staticmethod
    def _create_totalizador_item(tot: Any, valores_reais_por_periodo: Dict, valores_reais_por_nome: Dict,
                                meses: set, trimestres: set, anos: set, faturamento_data: Any = None, dre_items: List[Dict] = None) -> Dict:
        """Cria item totalizador com cálculos"""
        
        # Calcular totalizadores mensais
        valores_mensais = {}
        for mes in meses:
            total_mes = 0.0
            
            # Calcular baseado no tipo de totalizador
            if tot.nome_conta == "( = ) Receita Bruta":
                # Receita Bruta = Faturamento
                for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                    if dados['nome'] == "( + ) Faturamento":
                        total_mes = dados['valor']
                        break
            elif tot.nome_conta == "( = ) Receita Líquida":
                # Receita Líquida = Receita Bruta - Tributos
                receita_bruta = 0
                tributos = 0
                for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                    if dados['nome'] == "( + ) Faturamento":
                        receita_bruta = dados['valor']
                    elif dados['nome'] == "( - ) Tributos e deduções sobre a receita":
                        tributos = dados['valor']
                total_mes = receita_bruta + tributos  # tributos já vem negativo
            elif tot.nome_conta == "( = ) Resultado Bruto":
                # Resultado Bruto = Receita Líquida + CMV + CSP + CPV
                # CORREÇÃO: Usar o valor da linha totalizadora anterior (Receita Líquida)
                receita_liquida = 0
                cmv = 0
                csp = 0
                cpv = 0
                
                # Buscar Receita Líquida das linhas já processadas (totalizadores anteriores)
                for item in dre_items:
                    if item.get('nome') == "( = ) Receita Líquida":
                        receita_liquida = item.get('valores_mensais', {}).get(mes, 0)
                        break
                
                # Buscar valores das contas DRE N2 (CMV, CSP, CPV) dos valores reais
                for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                    if dados['nome'] == "( - ) CMV":
                        cmv = dados['valor']
                    elif dados['nome'] == "( - ) CSP":
                        csp = dados['valor']
                    elif dados['nome'] == "( - ) CPV":
                        cpv = dados['valor']
                
                # Calcular: Receita Líquida + CMV + CSP + CPV
                # NOTA: CMV, CSP e CPV já vêm com sinal negativo, então é uma soma
                total_mes = receita_liquida + cmv + csp + cpv
                
                # Log para debug (temporário)
                if mes in ["2025-02", "2025-01"]:  # Apenas para meses específicos
                    print(f"🔍 Resultado Bruto {mes}: RL={receita_liquida}, CMV={cmv}, CSP={csp}, CPV={cpv}, Total={total_mes}")
                    print(f"   📊 Receita Líquida encontrada: {receita_liquida}")
                    print(f"   📊 Valores das contas: CMV={cmv}, CSP={csp}, CPV={cpv}")
            else:
                # Para outros totalizadores, somar todas as contas anteriores
                for ordem, dados in valores_reais_por_periodo.get(mes, {}).items():
                    if dados['tipo'] in ['+', '-'] and ordem < tot.ordem:
                        total_mes += dados['valor']
            
            valores_mensais[mes] = total_mes
        
        # Calcular totalizadores trimestrais
        valores_trimestrais = {}
        for tri in trimestres:
            total_tri = 0.0
            # Somar os meses do trimestre
            for mes in meses:
                if mes.startswith(tri.split('-')[0]):  # Meses do mesmo ano
                    if tri.endswith('Q1') and mes.endswith(('-01', '-02', '-03')):
                        total_tri += valores_mensais.get(mes, 0)
                    elif tri.endswith('Q2') and mes.endswith(('-04', '-05', '-06')):
                        total_tri += valores_mensais.get(mes, 0)
                    elif tri.endswith('Q3') and mes.endswith(('-07', '-08', '-09')):
                        total_tri += valores_mensais.get(mes, 0)
                    elif tri.endswith('Q4') and mes.endswith(('-10', '-11', '-12')):
                        total_tri += valores_mensais.get(mes, 0)
            valores_trimestrais[tri] = total_tri

        
        # Calcular totalizadores anuais
        valores_anuais = {}
        for ano in anos:
            total_ano = 0.0
            # Somar os meses do ano
            for mes in meses:
                if mes.startswith(str(ano)):
                    total_ano += valores_mensais.get(mes, 0)
            valores_anuais[str(ano)] = total_ano

        
        # Calcular análises horizontais para totalizadores usando função já existente
        meses_ordenados = sorted(meses)
        trimestres_ordenados = sorted(trimestres)
        anos_ordenados = sorted(anos)
        
        # Usar função já existente para análises horizontais
        analises_horizontais = calcular_analises_horizontais_movimentacoes_postgresql(
            valores_mensais, valores_trimestrais, valores_anuais,
            meses_ordenados, trimestres_ordenados, anos_ordenados
        )
        
        analise_horizontal_mensal = analises_horizontais["horizontal_mensais"]
        analise_horizontal_trimestral = analises_horizontais["horizontal_trimestrais"]
        analise_horizontal_anual = analises_horizontais["horizontal_anuais"]
        
        # Análises verticais para totalizadores (baseada no faturamento)
        analise_vertical_mensal = {}
        analise_vertical_trimestral = {}
        analise_vertical_anual = {}
        
        if faturamento_data and faturamento_data.valores_mensais:
            faturamento_mensais = faturamento_data.valores_mensais or {}
            faturamento_trimestrais = faturamento_data.valores_trimestrais or {}
            faturamento_anuais = faturamento_data.valores_anuais or {}
            
            # Calcular AV usando função já existente
            for mes in meses:
                faturamento_mes = faturamento_mensais.get(mes, 0)
                valor_mes = valores_mensais.get(mes, 0)
                analise_vertical_mensal[mes] = calcular_analise_vertical_postgresql(valor_mes, faturamento_mes)
            
            for tri in trimestres:
                faturamento_tri = faturamento_trimestrais.get(tri, 0)
                valor_tri = valores_trimestrais.get(tri, 0)
                analise_vertical_trimestral[tri] = calcular_analise_vertical_postgresql(valor_tri, faturamento_tri)
            
            for ano in anos:
                faturamento_ano = faturamento_anuais.get(str(ano), 0)
                valor_ano = valores_anuais.get(str(ano), 0)
                analise_vertical_anual[str(ano)] = calcular_analise_vertical_postgresql(valor_ano, faturamento_ano)
        else:
            # Fallback se não houver dados de faturamento
            analise_vertical_mensal = {mes: "–" for mes in meses}
            analise_vertical_trimestral = {tri: "–" for tri in trimestres}
            analise_vertical_anual = {str(ano): "–" for ano in anos}
        
        return {
            "tipo": tot.tipo_operacao,
            "nome": tot.nome_conta,
            "ordem": tot.ordem,
            "expandivel": False,
            "valores_mensais": valores_mensais,
            "valores_trimestrais": valores_trimestrais,
            "valores_anuais": valores_anuais,
            "orcamentos_mensais": {},
            "orcamentos_trimestrais": {},
            "orcamentos_anuais": {},
            "orcamento_total": 0.0,
            "classificacoes": [],
            "analise_horizontal_mensal": analise_horizontal_mensal,
            "analise_vertical_mensal": analise_vertical_mensal,
            "analise_horizontal_trimestral": analise_horizontal_trimestral,
            "analise_vertical_trimestral": analise_vertical_trimestral,
            "analise_horizontal_anual": analise_horizontal_anual,
            "analise_vertical_anual": analise_vertical_anual
        }
