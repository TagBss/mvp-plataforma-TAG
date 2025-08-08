import pandas as pd
from .data_processor import calcular_totais_por_periodo, calcular_totalizadores
from .analysis_helper import calcular_analises_completas
from .structure_helper import carregar_estrutura_dfc, extrair_nome_conta

def criar_linha_conta_dfc(nome, tipo, totalizador_nome, valores_mensais, valores_trimestrais, 
                          valores_anuais, orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                          valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                          totalizadores_mensais, totalizadores_trimestrais, totalizadores_anuais,
                          totalizadores_orc_mensais, totalizadores_orc_trimestrais, totalizadores_orc_anuais,
                          totalizadores_totais, totalizadores_orc_totais, get_classificacoes):
    """Cria uma linha de conta para DFC"""
    
    def safe_round(valor):
        try:
            if pd.isna(valor) or valor is None:
                return 0
            return round(float(valor), 0)
        except (ValueError, TypeError):
            return 0
    
    def safe_get_valor(valores_dict, mes, nome):
        """Safely get value from dictionary or direct value"""
        try:
            if isinstance(valores_dict, dict):
                return valores_dict.get(nome, 0)
            else:
                return valores_dict if valores_dict else 0
        except:
            return 0
    
    valores_mes = {mes: safe_round(safe_get_valor(valores_mensais.get(mes, {}), mes, nome)) for mes in meses_unicos}
    valores_tri = {tri: safe_round(safe_get_valor(valores_trimestrais.get(tri, {}), tri, nome)) for tri in trimestres_unicos}
    valores_ano = {str(ano): safe_round(safe_get_valor(valores_anuais.get(str(ano), {}), str(ano), nome)) for ano in anos_unicos}
    orcamentos_mes = {mes: safe_round(safe_get_valor(orcamentos_mensais.get(mes, {}), mes, nome)) for mes in meses_unicos}
    orcamentos_tri = {tri: safe_round(safe_get_valor(orcamentos_trimestrais.get(tri, {}), tri, nome)) for tri in trimestres_unicos}
    orcamentos_ano = {str(ano): safe_round(safe_get_valor(orcamentos_anuais.get(str(ano), {}), str(ano), nome)) for ano in anos_unicos}

    # Usar .get() para evitar KeyError se o nome não existir
    valores_total = valores_totais.get(nome, 0)
    orcamento_total_item = orcamentos_totais.get(nome, 0)

    # Calcular análises
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, valores_total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total_item,
        meses_unicos, trimestres_unicos, anos_unicos,
        totalizadores_totais.get(totalizador_nome, 0)
    )

    return {
        "tipo": tipo,
        "nome": nome,
        "valor": valores_total,
        "valores_mensais": valores_mes,
        "valores_trimestrais": valores_tri,
        "valores_anuais": valores_ano,
        "orcamentos_mensais": orcamentos_mes,
        "orcamentos_trimestrais": orcamentos_tri,
        "orcamentos_anuais": orcamentos_ano,
        "orcamento_total": orcamento_total_item,
        **analises,
        "classificacoes": get_classificacoes(nome)
    }

def criar_item_nivel_0_dfc(nome, tipo="=", meses_unicos=None, trimestres_unicos=None, anos_unicos=None):
    """Cria um item de nível 0 para DFC (saldo inicial, movimentações, saldo final)"""
    if meses_unicos is None:
        meses_unicos = []
    if trimestres_unicos is None:
        trimestres_unicos = []
    if anos_unicos is None:
        anos_unicos = []
        
    return {
        "tipo": tipo,
        "nome": nome,
        "valor": 0,  # Placeholder
        "valores_mensais": {mes: 0 for mes in meses_unicos},
        "valores_trimestrais": {tri: 0 for tri in trimestres_unicos},
        "valores_anuais": {str(ano): 0 for ano in anos_unicos},
        "orcamentos_mensais": {mes: 0 for mes in meses_unicos},
        "orcamentos_trimestrais": {tri: 0 for tri in trimestres_unicos},
        "orcamentos_anuais": {str(ano): 0 for ano in anos_unicos},
        "orcamento_total": 0,
        "vertical_mensais": {mes: "–" for mes in meses_unicos},
        "vertical_trimestrais": {tri: "–" for tri in trimestres_unicos},
        "vertical_anuais": {str(ano): "–" for ano in anos_unicos},
        "vertical_total": "–",
        "horizontal_mensais": {mes: "–" for mes in meses_unicos},
        "horizontal_trimestrais": {tri: "–" for tri in trimestres_unicos},
        "horizontal_anuais": {str(ano): "–" for ano in anos_unicos},
        "vertical_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
        "vertical_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
        "vertical_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
        "vertical_orcamentos_total": "–",
        "horizontal_orcamentos_mensais": {mes: "–" for mes in meses_unicos},
        "horizontal_orcamentos_trimestrais": {tri: "–" for tri in trimestres_unicos},
        "horizontal_orcamentos_anuais": {str(ano): "–" for ano in anos_unicos},
        "real_vs_orcamento_mensais": {mes: "–" for mes in meses_unicos},
        "real_vs_orcamento_trimestrais": {tri: "–" for tri in trimestres_unicos},
        "real_vs_orcamento_anuais": {str(ano): "–" for ano in anos_unicos},
        "real_vs_orcamento_total": "–",
        "classificacoes": []
    }

def preparar_dados_por_periodo(totais, contas_dfc, meses_unicos, trimestres_unicos, anos_unicos):
    """Prepara os dados organizados por período"""
    
    valores_mensais = {
        mes: {nome: totais['total_real_por_mes'].get(mes, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for mes in meses_unicos
    }
    orcamentos_mensais = {
        mes: {nome: totais['total_orc_por_mes'].get(mes, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for mes in meses_unicos
    }

    valores_trimestrais = {
        tri: {nome: totais['total_real_por_tri'].get(tri, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for tri in trimestres_unicos
    }
    orcamentos_trimestrais = {
        tri: {nome: totais['total_orc_por_tri'].get(tri, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for tri in trimestres_unicos
    }

    valores_anuais = {
        str(ano): {nome: totais['total_real_por_ano'].get(ano, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for ano in anos_unicos
    }
    orcamentos_anuais = {
        str(ano): {nome: totais['total_orc_por_ano'].get(ano, {}).get(nome, 0.0) for nome, _ in contas_dfc}
        for ano in anos_unicos
    }

    valores_totais = {nome: totais['total_geral_real'].get(nome, 0.0) for nome, _ in contas_dfc}
    orcamentos_totais = {nome: totais['total_geral_orc'].get(nome, 0.0) for nome, _ in contas_dfc}

    return {
        'valores_mensais': valores_mensais,
        'orcamentos_mensais': orcamentos_mensais,
        'valores_trimestrais': valores_trimestrais,
        'orcamentos_trimestrais': orcamentos_trimestrais,
        'valores_anuais': valores_anuais,
        'orcamentos_anuais': orcamentos_anuais,
        'valores_totais': valores_totais,
        'orcamentos_totais': orcamentos_totais
    }

def calcular_totalizadores_por_periodo(valores_mensais, valores_trimestrais, valores_anuais, 
                                      orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                                      valores_totais, orcamentos_totais, estrutura_dfc, 
                                      meses_unicos, trimestres_unicos, anos_unicos):
    """Calcula totalizadores para todos os períodos"""
    totalizadores_mensais = {}
    for mes in meses_unicos:
        totalizadores_mensais[mes] = calcular_totalizadores(valores_mensais[mes], estrutura_dfc)

    totalizadores_trimestrais = {}
    for tri in trimestres_unicos:
        totalizadores_trimestrais[tri] = calcular_totalizadores(valores_trimestrais[tri], estrutura_dfc)

    totalizadores_anuais = {}
    for ano in anos_unicos:
        totalizadores_anuais[ano] = calcular_totalizadores(valores_anuais[str(ano)], estrutura_dfc)

    # Totalizadores para orçamentos
    totalizadores_orc_mensais = {}
    for mes in meses_unicos:
        totalizadores_orc_mensais[mes] = calcular_totalizadores(orcamentos_mensais[mes], estrutura_dfc)

    totalizadores_orc_trimestrais = {}
    for tri in trimestres_unicos:
        totalizadores_orc_trimestrais[tri] = calcular_totalizadores(orcamentos_trimestrais[tri], estrutura_dfc)

    totalizadores_orc_anuais = {}
    for ano in anos_unicos:
        totalizadores_orc_anuais[ano] = calcular_totalizadores(orcamentos_anuais[str(ano)], estrutura_dfc)

    # Totalizador geral
    totalizadores_totais = calcular_totalizadores(valores_totais, estrutura_dfc)
    totalizadores_orc_totais = calcular_totalizadores(orcamentos_totais, estrutura_dfc)

    return {
        'totalizadores_mensais': totalizadores_mensais,
        'totalizadores_trimestrais': totalizadores_trimestrais,
        'totalizadores_anuais': totalizadores_anuais,
        'totalizadores_orc_mensais': totalizadores_orc_mensais,
        'totalizadores_orc_trimestrais': totalizadores_orc_trimestrais,
        'totalizadores_orc_anuais': totalizadores_orc_anuais,
        'totalizadores_totais': totalizadores_totais,
        'totalizadores_orc_totais': totalizadores_orc_totais
    }

def obter_totalizadores_ordenados(estrutura_dfc, filename):
    """Obtém totalizadores únicos ordenados por dfc_n1_id"""
    totalizadores_unicos = set()
    for item in estrutura_dfc:
        if item["totalizador"]:
            totalizadores_unicos.add(item["totalizador"])
    
    # Carregar estrutura dfc_n1 para ordenação
    df_estrutura_n1 = pd.read_excel(filename, sheet_name="dfc_n1")
    mapeamento_n1_ordenacao = {}
    for _, row in df_estrutura_n1.iterrows():
        dfc_n1 = str(row.get('dfc_n1', ''))
        dfc_n1_id = row.get('dfc_n1_id', 0)
        if dfc_n1 and dfc_n1 != 'nan':
            nome_limpo = extrair_nome_conta(dfc_n1)
            mapeamento_n1_ordenacao[nome_limpo] = dfc_n1_id
    
    # Ordenar totalizadores por dfc_n1_id
    return sorted(
        totalizadores_unicos, 
        key=lambda x: mapeamento_n1_ordenacao.get(x, 9999)
    )

def calcular_valores_totalizador(contas_do_totalizador, estrutura_dfc, dados_por_periodo, 
                                meses_unicos, trimestres_unicos, anos_unicos):
    """Calcula valores de um totalizador manualmente"""
    valores_mensais_totalizador = {}
    valores_trimestrais_totalizador = {}
    valores_anuais_totalizador = {}
    orcamentos_mensais_totalizador = {}
    orcamentos_trimestrais_totalizador = {}
    orcamentos_anuais_totalizador = {}
    valores_totais_totalizador = 0
    orcamentos_totais_totalizador = 0
    
    for mes in meses_unicos:
        total_mes = 0
        total_orc_mes = 0
        for conta in contas_do_totalizador:
            valor = dados_por_periodo['valores_mensais'][mes].get(conta, 0)
            orc_valor = dados_por_periodo['orcamentos_mensais'][mes].get(conta, 0)
            total_mes += valor
            total_orc_mes += orc_valor
        valores_mensais_totalizador[mes] = total_mes
        orcamentos_mensais_totalizador[mes] = total_orc_mes
    
    for tri in trimestres_unicos:
        total_tri = 0
        total_orc_tri = 0
        for conta in contas_do_totalizador:
            valor = dados_por_periodo['valores_trimestrais'][tri].get(conta, 0)
            orc_valor = dados_por_periodo['orcamentos_trimestrais'][tri].get(conta, 0)
            total_tri += valor
            total_orc_tri += orc_valor
        valores_trimestrais_totalizador[tri] = total_tri
        orcamentos_trimestrais_totalizador[tri] = total_orc_tri
    
    for ano in anos_unicos:
        total_ano = 0
        total_orc_ano = 0
        for conta in contas_do_totalizador:
            valor = dados_por_periodo['valores_anuais'][str(ano)].get(conta, 0)
            orc_valor = dados_por_periodo['orcamentos_anuais'][str(ano)].get(conta, 0)
            total_ano += valor
            total_orc_ano += orc_valor
        valores_anuais_totalizador[str(ano)] = total_ano
        orcamentos_anuais_totalizador[str(ano)] = total_orc_ano
    
    # Calcular totais gerais
    for conta in contas_do_totalizador:
        valor = dados_por_periodo['valores_totais'].get(conta, 0)
        orc_valor = dados_por_periodo['orcamentos_totais'].get(conta, 0)
        valores_totais_totalizador += valor
        orcamentos_totais_totalizador += orc_valor
    
    return {
        'valores_mensais': valores_mensais_totalizador,
        'valores_trimestrais': valores_trimestrais_totalizador,
        'valores_anuais': valores_anuais_totalizador,
        'orcamentos_mensais': orcamentos_mensais_totalizador,
        'orcamentos_trimestrais': orcamentos_trimestrais_totalizador,
        'orcamentos_anuais': orcamentos_anuais_totalizador,
        'valores_totais': valores_totais_totalizador,
        'orcamentos_totais': orcamentos_totais_totalizador
    }

def criar_totalizadores_dinamicos(totalizadores_ordenados, estrutura_dfc, dados_por_periodo,
                                 totalizadores_por_periodo, meses_unicos, trimestres_unicos, anos_unicos,
                                 get_classificacoes):
    """Cria totalizadores dinâmicos com suas classificações"""
    totalizadores_dinamicos = {}
    
    for totalizador_nome in totalizadores_ordenados:
        # Encontrar todas as contas que pertencem a este totalizador
        contas_do_totalizador = [item["nome"] for item in estrutura_dfc if item["totalizador"] == totalizador_nome]
        
        # Calcular valores do totalizador
        valores_totalizador = calcular_valores_totalizador(
            contas_do_totalizador, estrutura_dfc, dados_por_periodo,
            meses_unicos, trimestres_unicos, anos_unicos
        )
        
        # Criar o totalizador usando helper
        totalizador = criar_linha_conta_dfc(
            totalizador_nome, "=", totalizador_nome,
            valores_totalizador['valores_mensais'], valores_totalizador['valores_trimestrais'], valores_totalizador['valores_anuais'],
            valores_totalizador['orcamentos_mensais'], valores_totalizador['orcamentos_trimestrais'], valores_totalizador['orcamentos_anuais'],
            {totalizador_nome: valores_totalizador['valores_totais']}, {totalizador_nome: valores_totalizador['orcamentos_totais']}, 
            meses_unicos, trimestres_unicos, anos_unicos,
            totalizadores_por_periodo['totalizadores_mensais'], totalizadores_por_periodo['totalizadores_trimestrais'], totalizadores_por_periodo['totalizadores_anuais'],
            totalizadores_por_periodo['totalizadores_orc_mensais'], totalizadores_por_periodo['totalizadores_orc_trimestrais'], totalizadores_por_periodo['totalizadores_orc_anuais'],
            totalizadores_por_periodo['totalizadores_totais'], totalizadores_por_periodo['totalizadores_orc_totais'], get_classificacoes
        )
        
        # Adicionar as contas filhas como classificações
        classificacoes = []
        contas_dfc = [(item["nome"], item["tipo"]) for item in estrutura_dfc]
        
        for nome_conta in contas_do_totalizador:
            conta_info = next((conta for conta in contas_dfc if conta[0] == nome_conta), None)
            if conta_info:
                nome, tipo = conta_info
                conta = criar_linha_conta_dfc(
                    nome, tipo, totalizador_nome,
                    dados_por_periodo['valores_mensais'], dados_por_periodo['valores_trimestrais'], dados_por_periodo['valores_anuais'],
                    dados_por_periodo['orcamentos_mensais'], dados_por_periodo['orcamentos_trimestrais'], dados_por_periodo['orcamentos_anuais'],
                    dados_por_periodo['valores_totais'], dados_por_periodo['orcamentos_totais'], meses_unicos, trimestres_unicos, anos_unicos,
                    totalizadores_por_periodo['totalizadores_mensais'], totalizadores_por_periodo['totalizadores_trimestrais'], totalizadores_por_periodo['totalizadores_anuais'],
                    totalizadores_por_periodo['totalizadores_orc_mensais'], totalizadores_por_periodo['totalizadores_orc_trimestrais'], totalizadores_por_periodo['totalizadores_orc_anuais'],
                    totalizadores_por_periodo['totalizadores_totais'], totalizadores_por_periodo['totalizadores_orc_totais'], get_classificacoes
                )
                classificacoes.append(conta)
        
        totalizador["classificacoes"] = classificacoes
        totalizadores_dinamicos[totalizador_nome] = totalizador
    
    return totalizadores_dinamicos

def calcular_saldo_dfc(origem: str, mes_filtro: str = None):
    """Calcula saldo genérico baseado na origem para DFC"""
    from .cache_helper import get_cached_df
    from .data_processor import calcular_mom
    from .analysis_helper import calcular_pmr_pmp
    
    filename = "db_bluefit - Copia.xlsx"
    
    try:
        df = get_cached_df(filename)
        if df is None:
            return {"error": "Erro ao ler o arquivo Excel."}

        # Validação das colunas obrigatórias
        required_columns = ["valor", "origem", "DFC_n1"]
        if not all(col in df.columns for col in required_columns):
            return {"error": f"A planilha deve conter as colunas: {', '.join(required_columns)}"}

        # Identificar coluna de data
        date_column = next((col for col in df.columns if col.lower() == "data"), None)
        if not date_column:
            return {"error": "Coluna de data não encontrada"}

        # Processar dados
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=[date_column, "valor"])

        # Filtrar apenas contas diferentes de DFC_n1 "Movimentação entre Contas"
        df_con = df[
            (df["DFC_n1"] != "Movimentação entre Contas") & 
            (df["DFC_n1"].notna())
        ].copy()

        # Filtrar pela origem dinâmica para MoM (NÃO filtra por mês)
        df_mom = df_con[df_con["origem"] == origem].copy()

        # Calcular MoM SEM filtro de mês (sempre retorna todos os meses)
        mom_data = calcular_mom(df_mom, date_column, origem)

        # Filtrar pela origem dinâmica para saldo (pode filtrar por mês)
        df_filtrado = df_con[df_con["origem"] == origem].copy()
        if mes_filtro:
            df_filtrado = df_filtrado[
                df_filtrado[date_column].dt.strftime("%Y-%m") == mes_filtro
            ]

        if df_filtrado.empty:
            return {
                "error": f"Não foram encontrados registros com origem '{origem}'",
                "total_passado": 0,
                "total_futuro": 0,
                "saldo_total": 0,
                "anos_disponiveis": [],
                "meses_disponiveis": []
            }

        hoje = pd.Timestamp.now().normalize()

        # Soma dos valores
        total_passado = df_filtrado[df_filtrado[date_column] < hoje]["valor"].sum()
        total_futuro = df_filtrado[df_filtrado[date_column] >= hoje]["valor"].sum()
        saldo_total = total_passado + total_futuro

        total_registros = len(df_filtrado)
        registros_passados = len(df_filtrado[df_filtrado[date_column] < hoje])
        registros_futuros = len(df_filtrado[df_filtrado[date_column] >= hoje])

        # Anos e meses disponíveis
        if not mes_filtro:
            # Se for todo o período, pegue todos os meses/anos disponíveis do df_con (toda a origem)
            anos_disponiveis = sorted(df_con[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_con[date_column].dt.strftime("%Y-%m").unique().tolist())
        else:
            anos_disponiveis = sorted(df_filtrado[date_column].dt.year.unique().tolist())
            meses_disponiveis = sorted(df_filtrado[date_column].dt.strftime("%Y-%m").unique().tolist())

        # Calcular PMR/PMP
        pmr_pmp = calcular_pmr_pmp(df_con, origem)

        return {
            "success": True,
            "data": {
                "total_passado": round(total_passado, 2),
                "total_futuro": round(total_futuro, 2),
                "saldo_total": round(saldo_total, 2),
                "data_calculo": hoje.strftime("%Y-%m-%d"),
                "estatisticas": {
                    "total_registros": total_registros,
                    "registros_passados": registros_passados,
                    "registros_futuros": registros_futuros
                },
                "anos_disponiveis": anos_disponiveis,
                "meses_disponiveis": meses_disponiveis,
                "mom_analysis": mom_data,
                "pmr": pmr_pmp["pmr"],
                "pmp": pmr_pmp["pmp"]
            }
        }
        
    except Exception as e:
        return {"error": f"Erro ao calcular saldo: {str(e)}"} 

def calcular_analises_horizontais_movimentacoes(valores_mensais, valores_trimestrais, valores_anuais, meses_unicos, trimestres_unicos, anos_unicos):
    """Calcula análises horizontais para movimentações"""
    from .analysis_helper import calcular_analise_horizontal
    
    horizontal_mensais = {}
    for i, mes in enumerate(meses_unicos):
        if i == 0:
            horizontal_mensais[mes] = "–"
        else:
            horizontal_mensais[mes] = calcular_analise_horizontal(valores_mensais[mes], valores_mensais[meses_unicos[i-1]])

    horizontal_trimestrais = {}
    for i, tri in enumerate(trimestres_unicos):
        if i == 0:
            horizontal_trimestrais[tri] = "–"
        else:
            horizontal_trimestrais[tri] = calcular_analise_horizontal(valores_trimestrais[tri], valores_trimestrais[trimestres_unicos[i-1]])

    horizontal_anuais = {}
    for i, ano in enumerate(anos_unicos):
        if i == 0:
            horizontal_anuais[str(ano)] = "–"
        else:
            horizontal_anuais[str(ano)] = calcular_analise_horizontal(valores_anuais[str(ano)], valores_anuais[str(anos_unicos[i-1])])

    return {
        "horizontal_mensais": horizontal_mensais,
        "horizontal_trimestrais": horizontal_trimestrais,
        "horizontal_anuais": horizontal_anuais
    } 