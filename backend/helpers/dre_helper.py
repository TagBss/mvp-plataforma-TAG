import pandas as pd
from .data_processor import calcular_totais_por_periodo
from .analysis_helper import calcular_analises_completas
from .structure_helper import carregar_estrutura_dre

def criar_linha_conta_dre(nome, tipo, valores_mensais, valores_trimestrais, valores_anuais,
                          orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                          valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                          get_classificacoes):
    """Cria uma linha de conta para DRE"""
    
    valores_mes = {mes: round(valores_mensais[mes][nome], 0) for mes in meses_unicos}
    valores_tri = {tri: round(valores_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
    valores_ano = {str(ano): round(valores_anuais[str(ano)][nome], 0) for ano in anos_unicos}
    orcamentos_mes = {mes: round(orcamentos_mensais[mes][nome], 0) for mes in meses_unicos}
    orcamentos_tri = {tri: round(orcamentos_trimestrais[tri][nome], 0) for tri in trimestres_unicos}
    orcamentos_ano = {str(ano): round(orcamentos_anuais[str(ano)][nome], 0) for ano in anos_unicos}

    valores_total = valores_totais[nome]
    orcamento_total = orcamentos_totais[nome]

    # Calcular análises usando faturamento como base vertical
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, valores_total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
        meses_unicos, trimestres_unicos, anos_unicos,
        valores_totais.get("Faturamento", 0)
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
        "orcamento_total": orcamento_total,
        **analises,
        "classificacoes": get_classificacoes(nome)
    }

def calcular_linha_totalizador_dre(nome, func, tipo="=", valores_totais=None, valores_mensais=None,
                                  valores_trimestrais=None, valores_anuais=None, orcamentos_totais=None,
                                  orcamentos_mensais=None, orcamentos_trimestrais=None, orcamentos_anuais=None,
                                  meses_unicos=None, trimestres_unicos=None, anos_unicos=None):
    """Calcula uma linha de totalizador para DRE"""
    
    if valores_totais is None:
        valores_totais = {}
    if valores_mensais is None:
        valores_mensais = {}
    if valores_trimestrais is None:
        valores_trimestrais = {}
    if valores_anuais is None:
        valores_anuais = {}
    if orcamentos_totais is None:
        orcamentos_totais = {}
    if orcamentos_mensais is None:
        orcamentos_mensais = {}
    if orcamentos_trimestrais is None:
        orcamentos_trimestrais = {}
    if orcamentos_anuais is None:
        orcamentos_anuais = {}
    if meses_unicos is None:
        meses_unicos = []
    if trimestres_unicos is None:
        trimestres_unicos = []
    if anos_unicos is None:
        anos_unicos = []
    
    total = round(func(valores_totais), 0)
    valores_mes = {mes: round(func(valores_mensais[mes]), 0) for mes in meses_unicos}
    valores_tri = {tri: round(func(valores_trimestrais[tri]), 0) for tri in trimestres_unicos}
    valores_ano = {str(ano): round(func(valores_anuais[str(ano)]), 0) for ano in anos_unicos}
    orcamentos_mes = {mes: round(func(orcamentos_mensais[mes]), 0) for mes in meses_unicos}
    orcamentos_tri = {tri: round(func(orcamentos_trimestrais[tri]), 0) for tri in trimestres_unicos}
    orcamentos_ano = {str(ano): round(func(orcamentos_anuais[str(ano)]), 0) for ano in anos_unicos}
    orcamento_total = round(func(orcamentos_totais), 0)

    # Calcular análises
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
        meses_unicos, trimestres_unicos, anos_unicos,
        valores_totais.get("Faturamento", 0)
    )

    return {
        "tipo": tipo,
        "nome": nome,
        "valor": total,
        "valores_mensais": valores_mes,
        "valores_trimestrais": valores_tri,
        "valores_anuais": valores_ano,
        "orcamentos_mensais": orcamentos_mes,
        "orcamentos_trimestrais": orcamentos_tri,
        "orcamentos_anuais": orcamentos_ano,
        "orcamento_total": orcamento_total,
        **analises,
        "classificacoes": []
    }

def get_classificacoes_dre(df_real, df_orc, dre_n2_name, meses_unicos, trimestres_unicos, anos_unicos,
                          valores_mensais, valores_trimestrais, valores_anuais, total_geral_real, total_geral_orc):
    """Obtém classificações para uma conta DRE específica"""
    sub_df_real = df_real[df_real["dre_n2"] == dre_n2_name]
    sub_df_orc = df_orc[df_orc["dre_n2"] == dre_n2_name]
    if sub_df_real.empty:
        return []

    classificacoes = []
    # Obter todas as classificações únicas (de realizado e orçamento)
    classificacoes_unicas = set(sub_df_real["classificacao"].unique())
    if not sub_df_orc.empty:
        classificacoes_unicas.update(sub_df_orc["classificacao"].unique())

    for classificacao in classificacoes_unicas:
        # Dados realizados
        grupo_real = sub_df_real[sub_df_real["classificacao"] == classificacao]
        
        # Dados orçamentários
        grupo_orc = sub_df_orc[sub_df_orc["classificacao"] == classificacao]

        # Calcular valores por período - REALIZADO
        valores_mes = {}
        for mes in meses_unicos:
            valores_mes[mes] = grupo_real[grupo_real["mes_ano"] == mes]["valor_original"].sum()

        valores_tri = {}
        for tri in trimestres_unicos:
            meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
            soma = sum(valores_mes.get(mes, 0) for mes in meses_do_tri)
            valores_tri[tri] = soma

        valores_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma = sum(valores_mes.get(mes, 0) for mes in meses_do_ano)
            valores_ano[str(ano)] = soma

        total_real = grupo_real["valor_original"].sum()

        # Calcular valores por período - ORÇAMENTO
        orcamentos_mes = {}
        for mes in meses_unicos:
            orcamentos_mes[mes] = grupo_orc[grupo_orc["mes_ano"] == mes]["valor_original"].sum()

        orcamentos_tri = {}
        for tri in trimestres_unicos:
            meses_do_tri = df_real[df_real["trimestre"] == tri]["mes_ano"].unique()
            soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_tri)
            orcamentos_tri[tri] = soma

        orcamentos_ano = {}
        for ano in anos_unicos:
            meses_do_ano = [m for m in meses_unicos if m.startswith(str(ano))]
            soma = sum(orcamentos_mes.get(mes, 0) for mes in meses_do_ano)
            orcamentos_ano[str(ano)] = soma

        total_orc = grupo_orc["valor_original"].sum()

        # Calcular análises
        analises = calcular_analises_completas(
            valores_mes, valores_tri, valores_ano, total_real,
            orcamentos_mes, orcamentos_tri, orcamentos_ano, total_orc,
            meses_unicos, trimestres_unicos, anos_unicos,
            total_geral_real.get("Faturamento", 0)
        )

        classificacoes.append({
            "nome": classificacao,
            "valor": total_real,
            "valores_mensais": valores_mes,
            "valores_trimestrais": valores_tri,
            "valores_anuais": valores_ano,
            "orcamentos_mensais": orcamentos_mes,
            "orcamentos_trimestrais": orcamentos_tri,
            "orcamentos_anuais": orcamentos_ano,
            **analises
        })
    return classificacoes 

def criar_linha_dre_simplificada(item_estrutura, valores_mensais, valores_trimestrais, valores_anuais,
                                 orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                                 valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos,
                                 get_classificacoes, totalizadores=None):
    """Cria uma linha de conta para DRE com estrutura simplificada"""
    
    nome = item_estrutura["nome"]
    tipo = item_estrutura["tipo"]
    expandivel = item_estrutura["expandivel"]
    
    # Se for totalizador (=), usar valores calculados dinamicamente
    if tipo == "=" and totalizadores:
        valores_mes = {mes: totalizadores['totalizadores_mensais'][mes].get(nome, 0) for mes in meses_unicos}
        valores_tri = {tri: totalizadores['totalizadores_trimestrais'][tri].get(nome, 0) for tri in trimestres_unicos}
        valores_ano = {str(ano): totalizadores['totalizadores_anuais'][str(ano)].get(nome, 0) for ano in anos_unicos}
        orcamentos_mes = {mes: totalizadores['totalizadores_orc_mensais'][mes].get(nome, 0) for mes in meses_unicos}
        orcamentos_tri = {tri: totalizadores['totalizadores_orc_trimestrais'][tri].get(nome, 0) for tri in trimestres_unicos}
        orcamentos_ano = {str(ano): totalizadores['totalizadores_orc_anuais'][str(ano)].get(nome, 0) for ano in anos_unicos}
        valores_total = totalizadores['totalizadores_totais'].get(nome, 0)
        orcamento_total = totalizadores['totalizadores_orc_totais'].get(nome, 0)
    else:
        # Obter valores por período dos dados originais
        valores_mes = {mes: valores_mensais[mes].get(nome, 0) for mes in meses_unicos}
        valores_tri = {tri: valores_trimestrais[tri].get(nome, 0) for tri in trimestres_unicos}
        valores_ano = {str(ano): valores_anuais[str(ano)].get(nome, 0) for ano in anos_unicos}
        orcamentos_mes = {mes: orcamentos_mensais[mes].get(nome, 0) for mes in meses_unicos}
        orcamentos_tri = {tri: orcamentos_trimestrais[tri].get(nome, 0) for tri in trimestres_unicos}
        orcamentos_ano = {str(ano): orcamentos_anuais[str(ano)].get(nome, 0) for ano in anos_unicos}
        valores_total = valores_totais.get(nome, 0)
        orcamento_total = orcamentos_totais.get(nome, 0)

    # Calcular análises usando faturamento como base vertical
    analises = calcular_analises_completas(
        valores_mes, valores_tri, valores_ano, valores_total,
        orcamentos_mes, orcamentos_tri, orcamentos_ano, orcamento_total,
        meses_unicos, trimestres_unicos, anos_unicos,
        valores_totais.get("Faturamento", 0)
    )

    # Se for expansível, buscar classificações
    classificacoes = []
    if expandivel:
        classificacoes = get_classificacoes(nome)

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
        "orcamento_total": orcamento_total,
        "expandivel": expandivel,
        **analises,
        "classificacoes": classificacoes
    } 

def calcular_totalizadores_dre(estrutura_dre, valores_mensais, valores_trimestrais, valores_anuais,
                              orcamentos_mensais, orcamentos_trimestrais, orcamentos_anuais,
                              valores_totais, orcamentos_totais, meses_unicos, trimestres_unicos, anos_unicos):
    """Calcula totalizadores dinamicamente baseado nos operadores matemáticos"""
    
    # Inicializar totalizadores com zeros
    totalizadores_mensais = {mes: {} for mes in meses_unicos}
    totalizadores_trimestrais = {tri: {} for tri in trimestres_unicos}
    totalizadores_anuais = {str(ano): {} for ano in anos_unicos}
    totalizadores_totais = {}
    totalizadores_orc_mensais = {mes: {} for mes in meses_unicos}
    totalizadores_orc_trimestrais = {tri: {} for tri in trimestres_unicos}
    totalizadores_orc_anuais = {str(ano): {} for ano in anos_unicos}
    totalizadores_orc_totais = {}
    
    # Processar cada item da estrutura
    for item in estrutura_dre:
        nome = item["nome"]
        tipo = item["tipo"]
        
        # Se for um totalizador (=), calcular baseado nos itens anteriores
        if tipo == "=":
            # Encontrar todos os itens que contribuem para este totalizador
            contribuintes = []
            for i, item_anterior in enumerate(estrutura_dre):
                if item_anterior["nome"] == nome:
                    break
                if item_anterior["tipo"] != "=":  # Só itens que não são totalizadores
                    contribuintes.append(item_anterior)
            
            # Calcular totalizador para cada período
            for mes in meses_unicos:
                total = 0
                total_orc = 0
                for contribuinte in contribuintes:
                    valor = valores_mensais[mes].get(contribuinte["nome"], 0)
                    valor_orc = orcamentos_mensais[mes].get(contribuinte["nome"], 0)
                    
                    # Aplicar o operador matemático considerando o sinal do valor
                    if contribuinte["tipo"] in ["+", "+/-"]:
                        total += valor
                        total_orc += valor_orc
                    elif contribuinte["tipo"] == "-":
                        # Para itens com operador "-", sempre subtrair o valor absoluto
                        total -= abs(valor)
                        total_orc -= abs(valor_orc)
                
                totalizadores_mensais[mes][nome] = total
                totalizadores_orc_mensais[mes][nome] = total_orc
            
            for tri in trimestres_unicos:
                total = 0
                total_orc = 0
                for contribuinte in contribuintes:
                    valor = valores_trimestrais[tri].get(contribuinte["nome"], 0)
                    valor_orc = orcamentos_trimestrais[tri].get(contribuinte["nome"], 0)
                    
                    if contribuinte["tipo"] in ["+", "+/-"]:
                        total += valor
                        total_orc += valor_orc
                    elif contribuinte["tipo"] == "-":
                        total -= abs(valor)
                        total_orc -= abs(valor_orc)
                
                totalizadores_trimestrais[tri][nome] = total
                totalizadores_orc_trimestrais[tri][nome] = total_orc
            
            for ano in anos_unicos:
                total = 0
                total_orc = 0
                for contribuinte in contribuintes:
                    valor = valores_anuais[str(ano)].get(contribuinte["nome"], 0)
                    valor_orc = orcamentos_anuais[str(ano)].get(contribuinte["nome"], 0)
                    
                    if contribuinte["tipo"] in ["+", "+/-"]:
                        total += valor
                        total_orc += valor_orc
                    elif contribuinte["tipo"] == "-":
                        total -= abs(valor)
                        total_orc -= abs(valor_orc)
                
                totalizadores_anuais[str(ano)][nome] = total
                totalizadores_orc_anuais[str(ano)][nome] = total_orc
            
            # Calcular total geral
            total_geral = 0
            total_orc_geral = 0
            for contribuinte in contribuintes:
                valor = valores_totais.get(contribuinte["nome"], 0)
                valor_orc = orcamentos_totais.get(contribuinte["nome"], 0)
                
                if contribuinte["tipo"] in ["+", "+/-"]:
                    total_geral += valor
                    total_orc_geral += valor_orc
                elif contribuinte["tipo"] == "-":
                    total_geral -= abs(valor)
                    total_orc_geral -= abs(valor_orc)
            
            totalizadores_totais[nome] = total_geral
            totalizadores_orc_totais[nome] = total_orc_geral
    
    return {
        'totalizadores_mensais': totalizadores_mensais,
        'totalizadores_trimestrais': totalizadores_trimestrais,
        'totalizadores_anuais': totalizadores_anuais,
        'totalizadores_totais': totalizadores_totais,
        'totalizadores_orc_mensais': totalizadores_orc_mensais,
        'totalizadores_orc_trimestrais': totalizadores_orc_trimestrais,
        'totalizadores_orc_anuais': totalizadores_orc_anuais,
        'totalizadores_orc_totais': totalizadores_orc_totais
    } 

def identificar_custos_despesas_dinamicamente(estrutura_dre):
    """Identifica dinamicamente custos e despesas baseado na estrutura da DRE"""
    
    custos = []
    despesas = []
    
    # Encontrar os totalizadores principais
    resultado_bruto = None
    ebitda = None
    receita_liquida = None
    
    for item in estrutura_dre:
        if item["nome"] == "Resultado Bruto":
            resultado_bruto = item
        elif item["nome"] == "EBITDA":
            ebitda = item
        elif item["nome"] == "Receita Líquida":
            receita_liquida = item
    
    if not resultado_bruto or not ebitda:
        return custos, despesas
    
    # Encontrar a posição dos totalizadores na estrutura
    resultado_bruto_index = -1
    ebitda_index = -1
    receita_liquida_index = -1
    
    for i, item in enumerate(estrutura_dre):
        if item["nome"] == "Resultado Bruto":
            resultado_bruto_index = i
        elif item["nome"] == "EBITDA":
            ebitda_index = i
        elif item["nome"] == "Receita Líquida":
            receita_liquida_index = i
    
    if resultado_bruto_index == -1 or ebitda_index == -1:
        return custos, despesas
    
    # Custos: itens com operador "-" que estão entre Receita Líquida e Resultado Bruto
    # (excluindo tributos que estão entre Receita Bruta e Receita Líquida)
    for i in range(len(estrutura_dre)):
        item = estrutura_dre[i]
        if item["tipo"] == "-" and item["nome"] != "Resultado Bruto" and item["nome"] != "EBITDA":
            # Verificar se está entre Receita Líquida e Resultado Bruto (custos)
            if receita_liquida_index != -1 and resultado_bruto_index != -1:
                if receita_liquida_index < i < resultado_bruto_index:
                    custos.append(item["nome"])
            # Se não temos Receita Líquida, usar lógica alternativa
            elif resultado_bruto_index != -1:
                # Custos são itens com "-" que estão antes do Resultado Bruto
                # mas não são tributos (que estão no início)
                if i < resultado_bruto_index and "Tributos" not in item["nome"]:
                    custos.append(item["nome"])
    
    # Despesas: itens com operador "-" que estão entre Resultado Bruto e EBITDA
    for i in range(resultado_bruto_index + 1, ebitda_index):
        item = estrutura_dre[i]
        if item["tipo"] == "-" and item["nome"] != "EBITDA":
            despesas.append(item["nome"])
    
    return custos, despesas 