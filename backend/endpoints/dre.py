from fastapi import APIRouter, Request
from helpers.cache_helper import get_cached_df
from helpers.structure_helper import carregar_estrutura_dre, extrair_nome_conta
from helpers.data_processor import processar_dados_financeiros, separar_realizado_orcamento, calcular_totais_por_periodo
from helpers.analysis_helper import calcular_analises_completas
from helpers.dre_helper import criar_linha_conta_dre, calcular_linha_totalizador_dre, get_classificacoes_dre
import pandas as pd

router = APIRouter()

@router.get("/dre")
def get_dre_data(request: Request):
    filename = "financial-data-roriz.xlsx"

    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Carregar estrutura DRE dinamicamente
        estrutura_dre = carregar_estrutura_dre(filename)
        if not estrutura_dre:
            return {"error": "Não foi possível carregar a estrutura DRE da planilha"}

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
        required_columns = ["DRE_n2", "valor_original", "classificacao", "origem", "competencia"]
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
        if df_orc.empty:
            return {"error": "Não foram encontrados dados orçamentários na planilha"}

        # Calcular totais por período
        totais = calcular_totais_por_periodo(df_real, df_orc, meses_unicos, trimestres_unicos, anos_unicos, "DRE_n2", "valor_original")

        # Usar estrutura dinâmica ao invés da lista manual
        contas_dre = [(item["nome"], item["tipo"]) for item in estrutura_dre]

        valores_mensais = {
            mes: {nome: totais['total_real_por_mes'].get(mes, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }
        orcamentos_mensais = {
            mes: {nome: totais['total_orc_por_mes'].get(mes, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for mes in meses_unicos
        }

        valores_trimestrais = {
            tri: {nome: totais['total_real_por_tri'].get(tri, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }
        orcamentos_trimestrais = {
            tri: {nome: totais['total_orc_por_tri'].get(tri, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for tri in trimestres_unicos
        }

        valores_anuais = {
            str(ano): {nome: totais['total_real_por_ano'].get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }
        orcamentos_anuais = {
            str(ano): {nome: totais['total_orc_por_ano'].get(ano, {}).get(nome, 0.0) for nome, _ in contas_dre}
            for ano in anos_unicos
        }

        valores_totais = {nome: totais['total_geral_real'].get(nome, 0.0) for nome, _ in contas_dre}
        orcamentos_totais = {nome: totais['total_geral_orc'].get(nome, 0.0) for nome, _ in contas_dre}

        def get_classificacoes(dre_n2_name):
            return get_classificacoes_dre(
                df_real, df_orc, dre_n2_name, meses_unicos, trimestres_unicos, anos_unicos,
                valores_mensais, valores_trimestrais, valores_anuais, totais['total_geral_real'], totais['total_geral_orc']
            )

        # Criar estrutura dinâmica baseada nos totalizadores
        result = []
        
        # Obter todos os totalizadores únicos da estrutura
        totalizadores_unicos = list(set(item["totalizador"] for item in estrutura_dre))
        
        # Carregar estrutura dre_n1 para ordenação
        df_estrutura_n1 = pd.read_excel(filename, sheet_name="dre_n1")
        mapeamento_n1_ordenacao = {}
        for _, row in df_estrutura_n1.iterrows():
            dre_n1 = str(row.get('dre_n1', ''))
            dre_n1_id = row.get('dre_n1_id', 0)
            if dre_n1 and dre_n1 != 'nan':
                nome_limpo = extrair_nome_conta(dre_n1)
                mapeamento_n1_ordenacao[nome_limpo] = dre_n1_id
        
        # Ordenar totalizadores por dre_n1_id
        totalizadores_ordenados = sorted(
            totalizadores_unicos, 
            key=lambda x: mapeamento_n1_ordenacao.get(x, 9999)
        )
        
        # Criar totalizadores dinamicamente
        totalizadores_criados = {}
        for totalizador_nome in totalizadores_ordenados:
            # Encontrar todas as contas que pertencem a este totalizador
            contas_do_totalizador = [item for item in estrutura_dre if item["totalizador"] == totalizador_nome]
            
            if not contas_do_totalizador:
                continue
            
            # Criar função de cálculo dinâmica
            def func_calculo(valores_dict):
                total = 0
                for conta in contas_do_totalizador:
                    nome_conta = conta["nome"]
                    if nome_conta in valores_dict:
                        total += valores_dict[nome_conta]
                return total
            
            # Criar o totalizador
            totalizador = calcular_linha_totalizador_dre(
                totalizador_nome, func_calculo, "=", valores_totais, valores_mensais,
                valores_trimestrais, valores_anuais, orcamentos_totais, orcamentos_mensais,
                orcamentos_trimestrais, orcamentos_anuais, meses_unicos, trimestres_unicos, anos_unicos
            )
            
            # Adicionar as contas filhas como classificações
            classificacoes = []
            for conta in contas_do_totalizador:
                nome = conta["nome"]
                tipo = conta["tipo"]
                conta_item = criar_linha_conta_dre(
                    nome, tipo, valores_mensais, valores_trimestrais, valores_anuais,
                    orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                    valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                    get_classificacoes
                )
                classificacoes.append(conta_item)
            
            totalizador["classificacoes"] = classificacoes
            totalizadores_criados[totalizador_nome] = totalizador
            result.append(totalizador)

        # Calcular análise vertical para as classificações
        for item in result:
            if "classificacoes" in item and item["classificacoes"]:
                for classificacao in item["classificacoes"]:
                    # Encontrar o faturamento para cálculo da análise vertical
                    faturamento_total = valores_totais.get("Faturamento", 0)
                    if faturamento_total == 0:
                        # Se não encontrar "Faturamento", usar o primeiro valor disponível
                        faturamento_total = next(iter(valores_totais.values()), 0)
                    
                    classificacao["vertical_total"] = calcular_analises_completas(
                        classificacao["valores_mensais"], classificacao["valores_trimestrais"], 
                        classificacao["valores_anuais"], classificacao["valor"],
                        classificacao["orcamentos_mensais"], classificacao["orcamentos_trimestrais"], 
                        classificacao["orcamentos_anuais"], classificacao["orcamento_total"],
                        meses_unicos, trimestres_unicos, anos_unicos, faturamento_total
                    )["vertical_total"]

        return {
            "meses": meses_unicos,
            "trimestres": trimestres_unicos,
            "anos": anos_unicos,
            "data": result,
            "orcamentos_mensais": orcamentos_mensais,
            "orcamentos_trimestrais": orcamentos_trimestrais,
            "orcamentos_anuais": orcamentos_anuais,
            "orcamento_total": orcamentos_totais,
        }

    except Exception as e:
        return {"error": f"Erro ao processar a DRE: {str(e)}"}