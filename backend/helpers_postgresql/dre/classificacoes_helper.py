"""
Helper para funções de classificações do DRE N0
"""
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
from helpers_postgresql.dre.analysis_helper_postgresql import calcular_analise_horizontal_postgresql, calcular_analise_vertical_postgresql

class ClassificacoesHelper:
    """Helper para operações de classificações do DRE N0"""
    
    @staticmethod
    def fetch_classificacoes_data(connection: Connection, dre_n2_name: str, empresa_id: str = None) -> List[Any]:
        """Busca dados de classificações para uma conta DRE N2 específica usando fluxo padrão"""
        
        print(f"🔍 Buscando classificações para DRE N2: {dre_n2_name}")
        if empresa_id:
            print(f"🏢 Filtrando por empresa_id: {empresa_id}")
        else:
            print("⚠️ Nenhum empresa_id fornecido - retornando dados de todas as empresas")
        
        # FLUXO CORRIGIDO: financial_data → de_para → plano_de_contas → classificacao_dre_n2
        # CORREÇÃO CRÍTICA: Adicionar empresa_id em TODOS os JOINs para isolamento total
        # PROBLEMA IDENTIFICADO: Dados se misturavam entre empresas
        query = text("""
            SELECT DISTINCT 
                pc.nome_conta as classificacao,
                pc.nome_conta as nome,  -- 🆕 NOVO: Campo 'nome' para o frontend
                pc.nome_conta as descricao,  -- 🆕 NOVO: Campo 'descricao' para exibição
                fd.valor_original,
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                AND dp.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                AND pc.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            WHERE pc.classificacao_dre_n2 LIKE '%' || :dre_n2_name || '%'
            AND fd.classificacao IS NOT NULL 
            AND fd.classificacao::text <> ''
            AND fd.classificacao::text <> 'nan'
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            """ + ("AND fd.empresa_id = :empresa_id" if empresa_id else "") + """
            ORDER BY pc.nome_conta, TO_CHAR(fd.competencia, 'YYYY-MM')
        """)
        
        # Preparar parâmetros da query
        params = {"dre_n2_name": dre_n2_name}
        if empresa_id:
            params["empresa_id"] = empresa_id
        
        result = connection.execute(query, params)
        dados = result.fetchall()
        
        print(f"📊 Encontradas {len(dados)} classificações únicas para {dre_n2_name}")
        if empresa_id:
            print(f"🏢 Filtradas por empresa_id: {empresa_id}")
        
        # Mostrar algumas classificações encontradas para debug
        if dados:
            classificacoes_unicas = list(set([row.classificacao for row in dados]))
            print(f"🔍 Classificações encontradas: {classificacoes_unicas[:3]}...")
        
        return dados
    
    @staticmethod
    def fetch_faturamento_data(connection: Connection, empresa_id: str = None) -> List[Any]:
        """Busca dados de faturamento para análise vertical usando fluxo correto"""
        
        print(f"💰 Buscando dados de faturamento")
        if empresa_id:
            print(f"🏢 Filtrando por empresa_id: {empresa_id}")
        
        # CORREÇÃO CRÍTICA: Adicionar empresa_id em TODOS os JOINs para isolamento total
        # CORREÇÃO DO FILTRO: Usar padrão correto encontrado no debug
        faturamento_query = text("""
            SELECT 
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                SUM(fd.valor_original) as valor_faturamento
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                AND dp.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                AND pc.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            WHERE pc.classificacao_dre_n2 LIKE '%( + ) Faturamento%'  -- ✅ FILTRO CORRIGIDO
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            """ + ("AND fd.empresa_id = :empresa_id" if empresa_id else "") + """
            GROUP BY 
                TO_CHAR(fd.competencia, 'YYYY-MM'),
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)),
                EXTRACT(YEAR FROM fd.competencia)
        """)
        
        # Preparar parâmetros da query
        params = {}
        if empresa_id:
            params["empresa_id"] = empresa_id
        
        faturamento_result = connection.execute(faturamento_query, params)
        return faturamento_result.fetchall()

    @staticmethod
    def verificar_empresa_tem_faturamento(connection: Connection, empresa_id: str) -> bool:
        """Verifica se uma empresa tem estrutura de faturamento"""
        query = text("""
            SELECT COUNT(*) as total
            FROM dre_structure_n2 ds
            WHERE ds.empresa_id = :empresa_id
            AND (LOWER(ds.name) LIKE '%faturamento%' 
                 OR LOWER(ds.description) LIKE '%faturamento%')
        """)
        
        result = connection.execute(query, {"empresa_id": empresa_id})
        count = result.fetchone().total
        return count > 0
    
    @staticmethod
    def buscar_metrica_alternativa(connection: Connection, empresa_id: str) -> str:
        """Busca métrica alternativa para empresas sem faturamento"""
        # Para empresas de consultoria, usar 'Receita de Projetos' ou similar
        query = text("""
            SELECT ds.name, ds.description
            FROM dre_structure_n2 ds
            WHERE ds.empresa_id = :empresa_id
            AND (LOWER(ds.name) LIKE '%receita%' 
                 OR LOWER(ds.name) LIKE '%projeto%'
                 OR LOWER(ds.description) LIKE '%receita%'
                 OR LOWER(ds.description) LIKE '%projeto%')
            ORDER BY ds.order_index
            LIMIT 1
        """)
        
        result = connection.execute(query, {"empresa_id": empresa_id})
        row = result.fetchone()
        
        if row:
            return f"{row.name} ({row.description})"
        else:
            return "Receita Total"  # Fallback genérico

    @staticmethod
    def process_classificacoes(rows: List[Any], faturamento_rows: List[Any]) -> List[Dict]:
        """Processa classificações e retorna dados estruturados"""
        
        if not rows:
            return [], set(), set(), set()
        
        # Processar classificações
        classificacoes = []
        meses = set()
        trimestres = set()
        anos = set()
        
        # Agrupar por classificação
        classificacoes_agrupadas = {}
        for row in rows:
            classificacao = row.classificacao
            if classificacao not in classificacoes_agrupadas:
                classificacoes_agrupadas[classificacao] = {
                    'nome': row.nome,  # 🆕 CORREÇÃO: Usar campo 'nome' da query
                    'classificacao': classificacao,  # 🔄 MANTIDO: Campo original para compatibilidade
                    'descricao': row.descricao,  # 🆕 NOVO: Usar campo 'descricao' da query
                    'valores_mensais': {},
                    'valores_trimestrais': {},
                    'valores_anuais': {},
                    'total_lancamentos': 0,
                    'valor_total': 0
                }
            
            # Adicionar valores por período
            periodo_mensal = row.periodo_mensal
            periodo_trimestral = row.periodo_trimestral
            periodo_anual = row.periodo_anual
            valor = float(row.valor_original) if row.valor_original else 0
            
            # Mensal
            if periodo_mensal not in classificacoes_agrupadas[classificacao]['valores_mensais']:
                classificacoes_agrupadas[classificacao]['valores_mensais'][periodo_mensal] = 0
            classificacoes_agrupadas[classificacao]['valores_mensais'][periodo_mensal] += valor
            meses.add(periodo_mensal)
            
            # Trimestral
            if periodo_trimestral not in classificacoes_agrupadas[classificacao]['valores_trimestrais']:
                classificacoes_agrupadas[classificacao]['valores_trimestrais'][periodo_trimestral] = 0
            classificacoes_agrupadas[classificacao]['valores_trimestrais'][periodo_trimestral] += valor
            trimestres.add(periodo_trimestral)
            
            # Anual
            if periodo_anual not in classificacoes_agrupadas[classificacao]['valores_anuais']:
                classificacoes_agrupadas[classificacao]['valores_anuais'][periodo_anual] = 0
            classificacoes_agrupadas[classificacao]['valores_anuais'][periodo_anual] += valor
            anos.add(periodo_anual)
            
            # Totais
            classificacoes_agrupadas[classificacao]['total_lancamentos'] += 1
            classificacoes_agrupadas[classificacao]['valor_total'] += valor
        
        # Converter para lista e ordenar por valor total
        classificacoes = list(classificacoes_agrupadas.values())
        classificacoes.sort(key=lambda x: abs(x['valor_total']), reverse=True)
        
        return classificacoes, meses, trimestres, anos

    @staticmethod
    def fetch_nomes_por_classificacao(connection: Connection, dre_n2_name: str, nome_classificacao: str, empresa_id: str = None) -> List[Any]:
        """Busca dados de nomes (lançamentos) para uma classificação específica - NOVO NÍVEL DE EXPANSÃO"""
        
        print(f"🔍 Buscando nomes para classificação: {nome_classificacao} em DRE N2: {dre_n2_name}")
        if empresa_id:
            print(f"🏢 Filtrando por empresa_id: {empresa_id}")
        else:
            print("⚠️ Nenhum empresa_id fornecido - retornando dados de todas as empresas")
        
        # FLUXO: financial_data → de_para → plano_de_contas → classificacao_dre_n2 → nome
        # NOVO NÍVEL: Agora buscamos por financial_data.nome para cada classificação
        query = text("""
            SELECT DISTINCT 
                fd.nome as nome_lancamento,
                fd.valor_original,
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                fd.classificacao,
                fd.observacao,
                fd.documento,
                fd.banco,
                fd.conta_corrente
            FROM financial_data fd
            JOIN de_para dp ON fd.classificacao = dp.descricao_origem
                AND dp.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            JOIN plano_de_contas pc ON dp.descricao_destino = pc.conta_pai
                AND pc.empresa_id = fd.empresa_id  -- ✅ ISOLAMENTO CRÍTICO
            WHERE pc.classificacao_dre_n2 LIKE '%' || :dre_n2_name || '%'
            AND pc.nome_conta = :nome_classificacao  -- ✅ FILTRO POR CLASSIFICAÇÃO ESPECÍFICA
            AND fd.nome IS NOT NULL 
            AND fd.nome::text <> ''
            AND fd.nome::text <> 'nan'
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            """ + ("AND fd.empresa_id = :empresa_id" if empresa_id else "") + """
            ORDER BY fd.nome, TO_CHAR(fd.competencia, 'YYYY-MM')
        """)
        
        # Preparar parâmetros da query
        params = {
            "dre_n2_name": dre_n2_name,
            "nome_classificacao": nome_classificacao
        }
        if empresa_id:
            params["empresa_id"] = empresa_id
        
        result = connection.execute(query, params)
        dados = result.fetchall()
        
        print(f"📊 Encontrados {len(dados)} nomes únicos para classificação {nome_classificacao} em {dre_n2_name}")
        if empresa_id:
            print(f"🏢 Filtrados por empresa_id: {empresa_id}")
        
        # Mostrar alguns nomes encontrados para debug
        if dados:
            nomes_unicos = list(set([row.nome_lancamento for row in dados]))
            print(f"🔍 Nomes encontrados: {nomes_unicos[:3]}...")
        
        return dados

    @staticmethod
    def process_nomes_por_classificacao(rows: List[Any], faturamento_rows: List[Any]) -> List[Dict]:
        """Processa nomes por classificação e retorna dados estruturados - NOVO NÍVEL DE EXPANSÃO"""
        
        if not rows:
            return [], set(), set(), set()
        
        # Processar nomes
        nomes = []
        meses = set()
        trimestres = set()
        anos = set()
        
        # Agrupar por nome (lançamento)
        nomes_agrupados = {}
        for row in rows:
            nome_lancamento = row.nome_lancamento
            if nome_lancamento not in nomes_agrupados:
                nomes_agrupados[nome_lancamento] = {
                    'nome': nome_lancamento,  # 🆕 CORREÇÃO: Campo 'nome' para o frontend
                    'nome_lancamento': nome_lancamento,  # 🔄 MANTIDO: Campo original para compatibilidade
                    'classificacao': row.classificacao,
                    'descricao': nome_lancamento,  # 🆕 NOVO: Campo 'descricao' para exibição
                    'valores_mensais': {},
                    'valores_trimestrais': {},
                    'valores_anuais': {},
                    'total_lancamentos': 0,
                    'valor_total': 0,
                    'observacao': row.observacao,
                    'documento': row.documento,
                    'banco': row.banco,
                    'conta_corrente': row.conta_corrente
                }
            
            # Adicionar valores por período
            periodo_mensal = row.periodo_mensal
            periodo_trimestral = row.periodo_trimestral
            periodo_anual = row.periodo_anual
            valor = float(row.valor_original) if row.valor_original else 0
            
            # Mensal
            if periodo_mensal not in nomes_agrupados[nome_lancamento]['valores_mensais']:
                nomes_agrupados[nome_lancamento]['valores_mensais'][periodo_mensal] = 0
            nomes_agrupados[nome_lancamento]['valores_mensais'][periodo_mensal] += valor
            meses.add(periodo_mensal)
            
            # Trimestral
            if periodo_trimestral not in nomes_agrupados[nome_lancamento]['valores_trimestrais']:
                nomes_agrupados[nome_lancamento]['valores_trimestrais'][periodo_trimestral] = 0
            nomes_agrupados[nome_lancamento]['valores_trimestrais'][periodo_trimestral] += valor
            trimestres.add(periodo_trimestral)
            
            # Anual
            if periodo_anual not in nomes_agrupados[nome_lancamento]['valores_anuais']:
                nomes_agrupados[nome_lancamento]['valores_anuais'][periodo_anual] = 0
            nomes_agrupados[nome_lancamento]['valores_anuais'][periodo_anual] += valor
            anos.add(periodo_anual)
            
            # Totais
            nomes_agrupados[nome_lancamento]['total_lancamentos'] += 1
            nomes_agrupados[nome_lancamento]['valor_total'] += valor
        
        # Converter para lista e ordenar por valor total
        nomes = list(nomes_agrupados.values())
        nomes.sort(key=lambda x: abs(x['valor_total']), reverse=True)
        
        return nomes, meses, trimestres, anos
