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
    def fetch_classificacoes_data(connection: Connection, dre_n2_name: str) -> List[Any]:
        """Busca dados de classificações para uma conta DRE N2 específica"""
        query = text("""
            SELECT 
                fd.classificacao,
                fd.valor_original,
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual
            FROM financial_data fd
            WHERE fd.dre_n2 = :dre_n2_name
            AND fd.classificacao IS NOT NULL 
            AND fd.classificacao::text <> ''
            AND fd.classificacao::text <> 'nan'
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            ORDER BY fd.classificacao, fd.competencia
        """)
        
        result = connection.execute(query, {"dre_n2_name": dre_n2_name})
        return result.fetchall()
    
    @staticmethod
    def fetch_faturamento_data(connection: Connection) -> List[Any]:
        """Busca dados de faturamento para análise vertical"""
        faturamento_query = text("""
            SELECT 
                TO_CHAR(fd.competencia, 'YYYY-MM') as periodo_mensal,
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)) as periodo_trimestral,
                EXTRACT(YEAR FROM fd.competencia)::text as periodo_anual,
                SUM(fd.valor_original) as valor_faturamento
            FROM financial_data fd
            WHERE fd.dre_n2 = '( + ) Faturamento'
            AND fd.valor_original IS NOT NULL 
            AND fd.competencia IS NOT NULL
            GROUP BY 
                TO_CHAR(fd.competencia, 'YYYY-MM'),
                CONCAT(EXTRACT(YEAR FROM fd.competencia), '-Q', EXTRACT(QUARTER FROM fd.competencia)),
                EXTRACT(YEAR FROM fd.competencia)
        """)
        
        faturamento_result = connection.execute(faturamento_query)
        return faturamento_result.fetchall()
    
    @staticmethod
    def process_classificacoes(rows: List[Any], faturamento_rows: List[Any]) -> List[Dict]:
        """Processa dados de classificações para o formato esperado pelo frontend"""
        # Agrupar dados por classificação
        dados_por_classificacao = {}
        meses = set()
        trimestres = set()
        anos = set()
        
        for row in rows:
            nome_classificacao = row.classificacao
            periodo_mensal = row.periodo_mensal
            periodo_trimestral = row.periodo_trimestral
            periodo_anual = row.periodo_anual
            valor = float(row.valor_original) if row.valor_original is not None else 0.0
            
            if nome_classificacao not in dados_por_classificacao:
                dados_por_classificacao[nome_classificacao] = {
                    'mensais': {},
                    'trimestrais': {},
                    'anuais': {},
                    'valor_total': 0.0
                }
            
            # Adicionar valor ao período mensal
            if periodo_mensal:
                if periodo_mensal in dados_por_classificacao[nome_classificacao]['mensais']:
                    dados_por_classificacao[nome_classificacao]['mensais'][periodo_mensal] += valor
                else:
                    dados_por_classificacao[nome_classificacao]['mensais'][periodo_mensal] = valor
                meses.add(periodo_mensal)
            
            # Adicionar valor ao período trimestral
            if periodo_trimestral:
                if periodo_trimestral in dados_por_classificacao[nome_classificacao]['trimestrais']:
                    dados_por_classificacao[nome_classificacao]['trimestrais'][periodo_trimestral] += valor
                else:
                    dados_por_classificacao[nome_classificacao]['trimestrais'][periodo_trimestral] = valor
                trimestres.add(periodo_trimestral)
            
            # Adicionar valor ao período anual
            if periodo_anual:
                if periodo_anual in dados_por_classificacao[nome_classificacao]['anuais']:
                    dados_por_classificacao[nome_classificacao]['anuais'][periodo_anual] += valor
                else:
                    dados_por_classificacao[nome_classificacao]['anuais'][periodo_anual] = valor
                anos.add(periodo_anual)
            
            # Acumular valor total
            dados_por_classificacao[nome_classificacao]['valor_total'] += valor
        
        # Organizar valores de faturamento por período
        faturamento_mensal = {row.periodo_mensal: float(row.valor_faturamento) for row in faturamento_rows if row.periodo_mensal}
        faturamento_trimestral = {row.periodo_trimestral: float(row.valor_faturamento) for row in faturamento_rows if row.periodo_trimestral}
        faturamento_anual = {row.periodo_anual: float(row.valor_faturamento) for row in faturamento_rows if row.periodo_anual}
        
        # Criar itens de classificação
        classificacoes = []
        for nome_classificacao, dados in dados_por_classificacao.items():
            # Determinar tipo baseado no valor total (se é negativo ou positivo)
            tipo_classificacao = "-" if dados['valor_total'] < 0 else "+"
            
            print(f"  📝 Criando classificação: {nome_classificacao}, valor_total: {dados['valor_total']}, tipo: {tipo_classificacao}")
            
            classificacao_item = ClassificacoesHelper._create_classificacao_item(
                nome_classificacao, tipo_classificacao, dados
            )
            
            # Calcular análises
            ClassificacoesHelper._add_analyses_to_classificacao(
                classificacao_item, dados, faturamento_mensal, faturamento_trimestral, faturamento_anual
            )
            
            classificacoes.append(classificacao_item)
        
        return classificacoes, meses, trimestres, anos
    
    @staticmethod
    def _create_classificacao_item(nome_classificacao: str, tipo_classificacao: str, dados: Dict) -> Dict:
        """Cria item de classificação individual"""
        return {
            "tipo": tipo_classificacao,
            "nome": nome_classificacao,
            "expandivel": False,
            "valores_mensais": dados['mensais'],
            "valores_trimestrais": dados['trimestrais'],
            "valores_anuais": dados['anuais'],
            "orcamentos_mensais": {},
            "orcamentos_trimestrais": {},
            "orcamentos_anuais": {},
            "orcamento_total": 0.0,
            "classificacoes": []
        }
    
    @staticmethod
    def _add_analyses_to_classificacao(classificacao_item: Dict, dados: Dict, 
                                      faturamento_mensal: Dict, faturamento_trimestral: Dict, 
                                      faturamento_anual: Dict):
        """Adiciona análises horizontal e vertical ao item de classificação"""
        
        # Calcular análises horizontais
        horizontal_mensais = {}
        meses_ordenados = sorted(dados['mensais'].keys())
        for i, mes in enumerate(meses_ordenados):
            if i == 0:
                horizontal_mensais[mes] = "–"
            else:
                valor_atual = dados['mensais'][mes]
                valor_anterior = dados['mensais'][meses_ordenados[i-1]]
                horizontal_mensais[mes] = calcular_analise_horizontal_postgresql(valor_atual, valor_anterior)
        
        horizontal_trimestrais = {}
        trimestres_ordenados = sorted(dados['trimestrais'].keys())
        for i, tri in enumerate(trimestres_ordenados):
            if i == 0:
                horizontal_trimestrais[tri] = "–"
            else:
                valor_atual = dados['trimestrais'][tri]
                valor_anterior = dados['trimestrais'][trimestres_ordenados[i-1]]
                horizontal_trimestrais[tri] = calcular_analise_horizontal_postgresql(valor_atual, valor_anterior)
        
        horizontal_anuais = {}
        anos_ordenados = sorted(dados['anuais'].keys())
        for i, ano in enumerate(anos_ordenados):
            if i == 0:
                horizontal_anuais[ano] = "–"
            else:
                valor_atual = dados['anuais'][ano]
                valor_anterior = dados['anuais'][anos_ordenados[i-1]]
                horizontal_anuais[ano] = calcular_analise_horizontal_postgresql(valor_atual, valor_anterior)
        
        # Calcular análises verticais
        vertical_mensais = {}
        for mes, valor in dados['mensais'].items():
            base = faturamento_mensal.get(mes, 0)
            vertical_mensais[mes] = calcular_analise_vertical_postgresql(valor, base)
        
        vertical_trimestrais = {}
        for tri, valor in dados['trimestrais'].items():
            base = faturamento_trimestral.get(tri, 0)
            vertical_trimestrais[tri] = calcular_analise_vertical_postgresql(valor, base)
        
        vertical_anuais = {}
        for ano, valor in dados['anuais'].items():
            base = faturamento_anual.get(ano, 0)
            vertical_anuais[ano] = calcular_analise_vertical_postgresql(valor, base)
        
        # Adicionar análises ao item de classificação
        classificacao_item.update({
            "horizontal_mensais": horizontal_mensais,
            "horizontal_trimestrais": horizontal_trimestrais,
            "horizontal_anuais": horizontal_anuais,
            "vertical_mensais": vertical_mensais,
            "vertical_trimestrais": vertical_trimestrais,
            "vertical_anuais": vertical_anuais
        })
