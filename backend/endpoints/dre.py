from fastapi import APIRouter, Request
from helpers.cache_helper import get_cached_df
from helpers.structure_helper import carregar_estrutura_dre_simplificada, extrair_nome_conta, verificar_correspondencia_dados_estrutura, normalizar_nomes_contas
from helpers.data_processor import processar_dados_financeiros, separar_realizado_orcamento, calcular_totais_por_periodo
from helpers.analysis_helper import calcular_analises_completas
from helpers.dre_helper import criar_linha_dre_simplificada, get_classificacoes_dre, calcular_totalizadores_dre, identificar_custos_despesas_dinamicamente
import pandas as pd

router = APIRouter()

@router.get("/dre")
def get_dre_data(request: Request):
    filename = "db_bluefit - Copia.xlsx"

    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Carregar estrutura DRE simplificada
        estrutura_dre = carregar_estrutura_dre_simplificada(filename)
        if not estrutura_dre:
            return {"error": "Não foi possível carregar a estrutura DRE da planilha"}

        # Identificar custos e despesas dinamicamente
        custos, despesas = identificar_custos_despesas_dinamicamente(estrutura_dre)

        # Filtro por mês, se fornecido na query string
        mes_param = request.query_params.get("mes")
        if mes_param:
            # Garante que a coluna mes_ano existe antes de filtrar
            date_column = next((col for col in df.columns if col.lower() == "competencia"), None)
            if date_column:
                df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
                df["mes_ano"] = df[date_column].dt.to_period("M").astype(str)
                df = df[df["mes_ano"] == mes_param]
            else:
                return {"error": "Coluna de competência não encontrada para filtro de mês."}

        # Validação das colunas obrigatórias
        required_columns = ["dre_n2", "valor_original", "classificacao", "origem", "competencia"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        date_column = next((col for col in df.columns if col.lower() == "competencia"), None)
        if not date_column:
            return {"error": "Coluna de competência não encontrada"}

        # Processar dados financeiros
        df, meses_unicos, anos_unicos, trimestres_unicos = processar_dados_financeiros(df, date_column, "valor_original")

        # Separar realizado e orçamento
        df_real, df_orc = separar_realizado_orcamento(df, "origem")

        if df_real.empty:
            return {"error": "Não foram encontrados dados realizados na planilha"}
        
        # Verificar se há dados orçamentários - se não houver, criar estrutura vazia
        if df_orc.empty:
            # Criar DataFrame vazio com a mesma estrutura
            df_orc = df_real.copy()
            df_orc["valor_original"] = 0.0
            df_orc["origem"] = "ORC"

        # Calcular totais por período
        totais = calcular_totais_por_periodo(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos, "dre_n2", "valor_original")

        # Verificar e normalizar correspondência
        stats_inicial = verificar_correspondencia_dados_estrutura(df_real, estrutura_dre, 'dre_n2', 'DRE')
        
        # Tentar normalizar nomes se necessário
        if not stats_inicial["correspondencia_perfeita"]:
            df_real = normalizar_nomes_contas(df_real, 'dre_n2', estrutura_dre)
            df_orc = normalizar_nomes_contas(df_orc, 'dre_n2', estrutura_dre)
            
            # Recarregar totais após normalização
            totais = calcular_totais_por_periodo(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos, "dre_n2", "valor_original")

        # Preparar dados por período
        valores_mensais = {
            mes: {nome: totais['total_real_por_mes'].get(mes, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for mes in meses_unicos
        }
        orcamentos_mensais = {
            mes: {nome: totais['total_orc_por_mes'].get(mes, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for mes in meses_unicos
        }

        valores_trimestrais = {
            tri: {nome: totais['total_real_por_tri'].get(tri, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for tri in trimestres_unicos
        }
        orcamentos_trimestrais = {
            tri: {nome: totais['total_orc_por_tri'].get(tri, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for tri in trimestres_unicos
        }

        valores_anuais = {
            str(ano): {nome: totais['total_real_por_ano'].get(ano, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for ano in anos_unicos
        }
        orcamentos_anuais = {
            str(ano): {nome: totais['total_orc_por_ano'].get(ano, {}).get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
            for ano in anos_unicos
        }

        valores_totais = {nome: totais['total_geral_real'].get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}
        orcamentos_totais = {nome: totais['total_geral_orc'].get(nome, 0.0) for nome in [item["nome"] for item in estrutura_dre]}

        # Calcular totalizadores dinamicamente
        totalizadores = calcular_totalizadores_dre(
            estrutura_dre, valores_mensais, valores_trimestrais, valores_anuais,
            orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
            valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos
        )

        def get_classificacoes(dre_n2_name):
            return get_classificacoes_dre(
                df_real, df_orc, dre_n2_name, meses_unicos, trimestres_unicos, anos_unicos,
                valores_mensais, valores_trimestrais, valores_anuais, totais['total_geral_real'], totais['total_geral_orc']
            )

        # Criar estrutura simplificada
        result = []
        
        for item_estrutura in estrutura_dre:
            linha_dre = criar_linha_dre_simplificada(
                item_estrutura, valores_mensais, valores_trimestrais, valores_anuais,
                orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                get_classificacoes, totalizadores
            )
            result.append(linha_dre)

        return {
            "meses": meses_unicos,
            "trimestres": trimestres_unicos,
            "anos": anos_unicos,
            "data": result,
            "orcamentos_mensais": orcamentos_mensais,
            "orcamentos_trimestrais": orcamentos_trimestrais,
            "orcamentos_anuais": orcamentos_anuais,
            "orcamento_total": orcamentos_totais,
            "custos": custos,
            "despesas": despesas
        }

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}