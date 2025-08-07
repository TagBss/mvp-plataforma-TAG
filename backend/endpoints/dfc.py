from fastapi import APIRouter
from helpers.cache_helper import get_cached_df
from helpers.structure_helper import carregar_estrutura_dfc, extrair_nome_conta
from helpers.data_processor import processar_dados_financeiros, separar_realizado_orcamento, calcular_totais_por_periodo, calcular_totalizadores
from helpers.analysis_helper import calcular_analises_completas
from helpers.dfc_helper import (
    criar_linha_conta_dfc, criar_item_nivel_0_dfc, calcular_saldo_dfc,
    preparar_dados_por_periodo, calcular_totalizadores_por_periodo,
    obter_totalizadores_ordenados, criar_totalizadores_dinamicos,
    calcular_analises_horizontais_movimentacoes
)
import pandas as pd
import traceback

router = APIRouter()

@router.get("/dfc")
def get_dfc_data():
    filename = "financial-data-roriz.xlsx"

    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Validação das colunas obrigatórias
        required_columns = ["DFC_n2", "valor", "classificacao", "origem", "data"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        date_column = next((col for col in df.columns if col.lower() == "data"), None)
        if not date_column:
            return {"error": "Coluna de competência não encontrada"}

        # Processar dados financeiros
        df, meses_unicos, anos_unicos, trimestres_unicos = processar_dados_financeiros(df, date_column, "valor")

        # Separar realizado e orçamento
        df_real, df_orc = separar_realizado_orcamento(df, "origem")

        if df_real.empty:
            return {"error": "Não foram encontrados dados realizados na planilha"}
        if df_orc.empty:
            return {"error": "Não foram encontrados dados orçamentários na planilha"}

        # Calcular totais por período
        totais = calcular_totais_por_periodo(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos, "DFC_n2", "valor")

        # Carregar estrutura dinâmica DFC
        estrutura_dfc = carregar_estrutura_dfc(filename)
        if not estrutura_dfc:
            return {"error": "Não foi possível carregar a estrutura DFC da planilha"}
        
        # Criar lista de contas a partir da estrutura dinâmica
        contas_dfc = [(item["nome"], item["tipo"]) for item in estrutura_dfc]

        # Preparar dados por período usando helper
        dados_por_periodo = preparar_dados_por_periodo(totais, contas_dfc, meses_unicos, trimestres_unicos, anos_unicos)

        def get_classificacoes(dfc_n2_name):
            sub_df = df_real[df_real["DFC_n2"] == dfc_n2_name]
            if sub_df.empty:
                return []

            classificacoes = []
            for classificacao, grupo in sub_df.groupby("classificacao"):
                total_class = grupo["valor"].sum()
                
                # Calcular valores por período
                valores_mensais = {}
                orcamentos_mensais = {}
                for mes in meses_unicos:
                    real_mes = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["mes_ano"] == mes)]["valor"].sum()
                    orc_mes = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["mes_ano"] == mes)]["valor"].sum()
                    valores_mensais[mes] = real_mes
                    orcamentos_mensais[mes] = orc_mes
                
                valores_trimestrais = {}
                orcamentos_trimestrais = {}
                for tri in trimestres_unicos:
                    real_tri = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["trimestre"] == tri)]["valor"].sum()
                    orc_tri = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["trimestre"] == tri)]["valor"].sum()
                    valores_trimestrais[tri] = real_tri
                    orcamentos_trimestrais[tri] = orc_tri
                
                valores_anuais = {}
                orcamentos_anuais = {}
                for ano in anos_unicos:
                    real_ano = df_real[(df_real["DFC_n2"] == dfc_n2_name) & 
                                      (df_real["classificacao"] == classificacao) & 
                                      (df_real["ano"] == ano)]["valor"].sum()
                    orc_ano = df_orc[(df_orc["DFC_n2"] == dfc_n2_name) & 
                                    (df_orc["classificacao"] == classificacao) & 
                                    (df_orc["ano"] == ano)]["valor"].sum()
                    valores_anuais[str(ano)] = real_ano
                    orcamentos_anuais[str(ano)] = orc_ano
                
                # Calcular análises completas para as classificações
                # Usar o total do item pai (dfc_n2) como base para análise vertical
                total_item_pai = totais['total_geral_real'].get(dfc_n2_name, 0)
                if total_item_pai == 0:
                    # Se não encontrar o item pai, usar o total geral
                    total_item_pai = sum(totais['total_geral_real'].values())
                
                # Para análise vertical, usar o total do item pai como base
                analises_classificacao = calcular_analises_completas(
                    valores_mensais, valores_trimestrais, valores_anuais, total_class,
                    orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais, sum(orcamentos_mensais.values()),
                    meses_unicos, trimestres_unicos, anos_unicos, total_item_pai
                )
                
                classificacoes.append({
                    "nome": classificacao,
                    "valor": total_class,
                    "valores_mensais": valores_mensais,
                    "valores_trimestrais": valores_trimestrais,
                    "valores_anuais": valores_anuais,
                    "orcamentos_mensais": orcamentos_mensais,
                    "orcamentos_trimestrais": orcamentos_trimestrais,
                    "orcamentos_anuais": orcamentos_anuais,
                    "orcamento_total": sum(orcamentos_mensais.values()),
                    **analises_classificacao
                })
            return classificacoes

        # Calcular totalizadores por período usando helper
        totalizadores_por_periodo = calcular_totalizadores_por_periodo(
            dados_por_periodo['valores_mensais'], dados_por_periodo['valores_trimestrais'], dados_por_periodo['valores_anuais'],
            dados_por_periodo['orcamentos_mensais'], dados_por_periodo['orcamentos_trimestrais'], dados_por_periodo['orcamentos_anuais'],
            dados_por_periodo['valores_totais'], dados_por_periodo['orcamentos_totais'], estrutura_dfc,
            meses_unicos, trimestres_unicos, anos_unicos
        )

        # Obter totalizadores ordenados usando helper
        totalizadores_ordenados = obter_totalizadores_ordenados(estrutura_dfc, filename)

        # Criar totalizadores dinâmicos usando helper
        totalizadores_dinamicos = criar_totalizadores_dinamicos(
            totalizadores_ordenados, estrutura_dfc, dados_por_periodo,
            totalizadores_por_periodo, meses_unicos, trimestres_unicos, anos_unicos,
            get_classificacoes
        )

        # Criar estrutura hierárquica
        result = []

        # 1. SALDO INICIAL
        saldo_inicial = criar_item_nivel_0_dfc("Saldo inicial", "=", meses_unicos, trimestres_unicos, anos_unicos)
        
        # Calcular saldo inicial mês a mês (saldo final do mês anterior)
        saldo_acumulado = 0
        for mes in meses_unicos:
            saldo_inicial["valores_mensais"][mes] = saldo_acumulado
            saldo_acumulado += sum(totalizador["valores_mensais"][mes] for totalizador in totalizadores_dinamicos.values())
        
        # Calcular saldo inicial trimestre a trimestre
        saldo_acumulado_tri = 0
        for tri in trimestres_unicos:
            saldo_inicial["valores_trimestrais"][tri] = saldo_acumulado_tri
            saldo_acumulado_tri += sum(totalizador["valores_trimestrais"][tri] for totalizador in totalizadores_dinamicos.values())
        
        # Calcular saldo inicial ano a ano
        saldo_acumulado_ano = 0
        for ano in anos_unicos:
            saldo_inicial["valores_anuais"][str(ano)] = saldo_acumulado_ano
            saldo_acumulado_ano += sum(totalizador["valores_anuais"][str(ano)] for totalizador in totalizadores_dinamicos.values())
        
        # Fazer o mesmo para orçamentos
        saldo_acumulado_orc = 0
        for mes in meses_unicos:
            saldo_inicial["orcamentos_mensais"][mes] = saldo_acumulado_orc
            saldo_acumulado_orc += sum(totalizador["orcamentos_mensais"][mes] for totalizador in totalizadores_dinamicos.values())
        
        saldo_acumulado_orc_tri = 0
        for tri in trimestres_unicos:
            saldo_inicial["orcamentos_trimestrais"][tri] = saldo_acumulado_orc_tri
            saldo_acumulado_orc_tri += sum(totalizador["orcamentos_trimestrais"][tri] for totalizador in totalizadores_dinamicos.values())
        
        saldo_acumulado_orc_ano = 0
        for ano in anos_unicos:
            saldo_inicial["orcamentos_anuais"][str(ano)] = saldo_acumulado_orc_ano
            saldo_acumulado_orc_ano += sum(totalizador["orcamentos_anuais"][str(ano)] for totalizador in totalizadores_dinamicos.values())
        
        # Calcular análises horizontais para saldo inicial
        analises_horizontais_saldo_inicial = calcular_analises_horizontais_movimentacoes(
            saldo_inicial["valores_mensais"], saldo_inicial["valores_trimestrais"], saldo_inicial["valores_anuais"],
            meses_unicos, trimestres_unicos, anos_unicos
        )
        saldo_inicial["horizontal_mensais"] = analises_horizontais_saldo_inicial["horizontal_mensais"]
        saldo_inicial["horizontal_trimestrais"] = analises_horizontais_saldo_inicial["horizontal_trimestrais"]
        saldo_inicial["horizontal_anuais"] = analises_horizontais_saldo_inicial["horizontal_anuais"]
        
        # Remover AV do nível 0
        saldo_inicial["vertical_mensais"] = {mes: "–" for mes in meses_unicos}
        saldo_inicial["vertical_trimestrais"] = {tri: "–" for tri in trimestres_unicos}
        saldo_inicial["vertical_anuais"] = {str(ano): "–" for ano in anos_unicos}
        saldo_inicial["vertical_total"] = "–"
        
        # Calcular AH para o total do saldo inicial
        saldo_inicial["horizontal_total"] = "–"  # Primeiro item não tem AH
        
        result.append(saldo_inicial)

        # 2. MOVIMENTAÇÕES
        movimentacoes = criar_item_nivel_0_dfc("Movimentações", "=", meses_unicos, trimestres_unicos, anos_unicos)
        
        # Calcular valores de movimentações como soma de todos os totalizadores dinâmicos
        for mes in meses_unicos:
            movimentacoes["valores_mensais"][mes] = sum(
                totalizador["valores_mensais"][mes] for totalizador in totalizadores_dinamicos.values()
            )
        for tri in trimestres_unicos:
            movimentacoes["valores_trimestrais"][tri] = sum(
                totalizador["valores_trimestrais"][tri] for totalizador in totalizadores_dinamicos.values()
            )
        for ano in anos_unicos:
            movimentacoes["valores_anuais"][str(ano)] = sum(
                totalizador["valores_anuais"][str(ano)] for totalizador in totalizadores_dinamicos.values()
            )
        
        # Atualizar valor total
        movimentacoes["valor"] = sum(
            totalizador["valor"] for totalizador in totalizadores_dinamicos.values()
        )
        
        # Calcular orçamentos de movimentações como soma de todos os totalizadores
        for mes in meses_unicos:
            movimentacoes["orcamentos_mensais"][mes] = sum(
                totalizador["orcamentos_mensais"][mes] for totalizador in totalizadores_dinamicos.values()
            )
        for tri in trimestres_unicos:
            movimentacoes["orcamentos_trimestrais"][tri] = sum(
                totalizador["orcamentos_trimestrais"][tri] for totalizador in totalizadores_dinamicos.values()
            )
        for ano in anos_unicos:
            movimentacoes["orcamentos_anuais"][str(ano)] = sum(
                totalizador["orcamentos_anuais"][str(ano)] for totalizador in totalizadores_dinamicos.values()
            )
        
        # Atualizar orçamento total
        movimentacoes["orcamento_total"] = sum(
            totalizador["orcamento_total"] for totalizador in totalizadores_dinamicos.values()
        )
        
        # Calcular análises horizontais para movimentações
        analises_horizontais = calcular_analises_horizontais_movimentacoes(
            movimentacoes["valores_mensais"], movimentacoes["valores_trimestrais"], movimentacoes["valores_anuais"],
            meses_unicos, trimestres_unicos, anos_unicos
        )
        movimentacoes["horizontal_mensais"] = analises_horizontais["horizontal_mensais"]
        movimentacoes["horizontal_trimestrais"] = analises_horizontais["horizontal_trimestrais"]
        movimentacoes["horizontal_anuais"] = analises_horizontais["horizontal_anuais"]
        
        # Remover AV das movimentações
        movimentacoes["vertical_mensais"] = {mes: "–" for mes in meses_unicos}
        movimentacoes["vertical_trimestrais"] = {tri: "–" for tri in trimestres_unicos}
        movimentacoes["vertical_anuais"] = {str(ano): "–" for ano in anos_unicos}
        movimentacoes["vertical_total"] = "–"
        
        # Calcular AH para o total das movimentações
        movimentacoes["horizontal_total"] = "–"  # Movimentações não têm AH no total
        
        # Adicionar todos os totalizadores dinâmicos como classificações de "Movimentações"
        movimentacoes["classificacoes"] = list(totalizadores_dinamicos.values())
        
        result.append(movimentacoes)

        # 3. SALDO FINAL
        saldo_final = criar_item_nivel_0_dfc("Saldo final", "=", meses_unicos, trimestres_unicos, anos_unicos)
        
        # Calcular saldo final mês a mês (saldo inicial + movimentação)
        for mes in meses_unicos:
            saldo_final["valores_mensais"][mes] = saldo_inicial["valores_mensais"][mes] + movimentacoes["valores_mensais"][mes]
        
        # Calcular saldo final trimestre a trimestre
        for tri in trimestres_unicos:
            saldo_final["valores_trimestrais"][tri] = saldo_inicial["valores_trimestrais"][tri] + movimentacoes["valores_trimestrais"][tri]
        
        # Calcular saldo final ano a ano
        for ano in anos_unicos:
            saldo_final["valores_anuais"][str(ano)] = saldo_inicial["valores_anuais"][str(ano)] + movimentacoes["valores_anuais"][str(ano)]
        
        # Saldo final total
        saldo_final["valor"] = movimentacoes["valor"]
        
        # Fazer o mesmo para orçamentos
        for mes in meses_unicos:
            saldo_final["orcamentos_mensais"][mes] = saldo_inicial["orcamentos_mensais"][mes] + movimentacoes["orcamentos_mensais"][mes]
        
        for tri in trimestres_unicos:
            saldo_final["orcamentos_trimestrais"][tri] = saldo_inicial["orcamentos_trimestrais"][tri] + movimentacoes["orcamentos_trimestrais"][tri]
        
        for ano in anos_unicos:
            saldo_final["orcamentos_anuais"][str(ano)] = saldo_inicial["orcamentos_anuais"][str(ano)] + movimentacoes["orcamentos_anuais"][str(ano)]
        
        saldo_final["orcamento_total"] = movimentacoes["orcamento_total"]
        
        # Calcular análises horizontais para saldo final
        analises_horizontais_saldo_final = calcular_analises_horizontais_movimentacoes(
            saldo_final["valores_mensais"], saldo_final["valores_trimestrais"], saldo_final["valores_anuais"],
            meses_unicos, trimestres_unicos, anos_unicos
        )
        saldo_final["horizontal_mensais"] = analises_horizontais_saldo_final["horizontal_mensais"]
        saldo_final["horizontal_trimestrais"] = analises_horizontais_saldo_final["horizontal_trimestrais"]
        saldo_final["horizontal_anuais"] = analises_horizontais_saldo_final["horizontal_anuais"]
        
        # Remover AV do saldo final
        saldo_final["vertical_mensais"] = {mes: "–" for mes in meses_unicos}
        saldo_final["vertical_trimestrais"] = {tri: "–" for tri in trimestres_unicos}
        saldo_final["vertical_anuais"] = {str(ano): "–" for ano in anos_unicos}
        saldo_final["vertical_total"] = "–"
        
        # Calcular AH para o total do saldo final
        saldo_final["horizontal_total"] = "–"  # Saldo final não tem AH no total
        
        result.append(saldo_final)

        return {
            "meses": meses_unicos,
            "trimestres": trimestres_unicos,
            "anos": anos_unicos,
            "data": result,
            "orcamentos_mensais": dados_por_periodo['orcamentos_mensais'],
            "orcamentos_trimestrais": dados_por_periodo['orcamentos_trimestrais'],
            "orcamentos_anuais": dados_por_periodo['orcamentos_anuais'],
            "orcamento_total": dados_por_periodo['orcamentos_totais'],
        }

    except Exception as e:
        error_msg = f"Erro ao processar a DFC: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {"error": error_msg}

@router.get("/receber")
def get_caixa_saldo(mes: str = None):
    return calcular_saldo_dfc("CAR", mes)

@router.get("/pagar")
def get_pagar_saldo(mes: str = None):
    return calcular_saldo_dfc("CAP", mes)