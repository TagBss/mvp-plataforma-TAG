import pandas as pd
import re

def extrair_tipo_operacao(texto):
    """Extrai o tipo de operação de um texto como '( + ) Recebimentos Operacionais'"""
    if not texto or pd.isna(texto):
        return "="
    
    texto = str(texto).strip()
    
    # Padrões para diferentes tipos de operação
    padroes = [
        r'\(\s*\+\s*/\s*-\s*\)',  # ( + / - )
        r'\(\s*\+\s*\)',          # ( + )
        r'\(\s*-\s*\)',           # ( - )
        r'\(\s*=\s*\)',           # ( = )
        r'\(\+/-\)',              # (+/-)
        r'\(\+\)',                # (+)
        r'\(-\)',                  # (-)
        r'\(=\)',                 # (=)
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            tipo = match.group()
            # Limpar o tipo encontrado
            tipo = re.sub(r'[()\s]', '', tipo)
            return tipo
    
    return "="

def extrair_nome_conta(texto):
    """Extrai o nome da conta removendo os parênteses e tipos"""
    if not texto or pd.isna(texto):
        return ""
    
    texto = str(texto).strip()
    
    # Remover todos os padrões de tipo de operação
    padroes_para_remover = [
        r'\(\s*\+\s*/\s*-\s*\)',  # ( + / - )
        r'\(\s*\+\s*\)',          # ( + )
        r'\(\s*-\s*\)',           # ( - )
        r'\(\s*=\s*\)',           # ( = )
        r'\(\+/-\)',              # (+/-)
        r'\(\+\)',                # (+)
        r'\(-\)',                  # (-)
        r'\(=\)',                 # (=)
    ]
    
    for padrao in padroes_para_remover:
        texto = re.sub(padrao, '', texto)
    
    return texto.strip()

def carregar_estrutura_dfc(filename):
    """Carrega a estrutura DFC das abas dfc_n2 e dfc_n1 da planilha"""
    try:
        # Carregar estrutura dfc_n2
        df_estrutura_n2 = pd.read_excel(filename, sheet_name="dfc_n2")
        
        # Carregar estrutura dfc_n1 para ordenação
        df_estrutura_n1 = pd.read_excel(filename, sheet_name="dfc_n1")
        
        # Criar mapeamento de dfc_n1 para dfc_n1_id
        mapeamento_n1 = {}
        for _, row in df_estrutura_n1.iterrows():
            dfc_n1 = str(row.get('dfc_n1', ''))
            dfc_n1_id = row.get('dfc_n1_id', 0)
            if dfc_n1 and dfc_n1 != 'nan':
                mapeamento_n1[dfc_n1] = dfc_n1_id
        
        estrutura = []
        for _, row in df_estrutura_n2.iterrows():
            dfc_n2 = str(row.get('dfc_n2', ''))
            dfc_n1 = str(row.get('dfc_n1', ''))
            dfc_n2_id = row.get('dfc_n2_id', 0)
            
            if dfc_n2 and dfc_n2 != 'nan':
                nome = extrair_nome_conta(dfc_n2)
                tipo = extrair_tipo_operacao(dfc_n2)
                totalizador = extrair_nome_conta(dfc_n1) if dfc_n1 and dfc_n1 != 'nan' else ""
                
                estrutura.append({
                    "nome": nome,
                    "tipo": tipo,
                    "totalizador": totalizador,
                    "dfc_n2_id": dfc_n2_id,
                    "dfc_n1_id": mapeamento_n1.get(dfc_n1, 0)
                })
        
        # Ordenar por dfc_n1_id primeiro, depois por dfc_n2_id
        estrutura.sort(key=lambda x: (x["dfc_n1_id"], x["dfc_n2_id"]))
        
        return estrutura
    except Exception as e:
        print(f"❌ Erro ao carregar estrutura DFC: {e}")
        return []

def carregar_estrutura_dre(filename="financial-data-roriz.xlsx"):
    """Carrega a estrutura DRE das abas dre_n2 e dre_n1 da planilha"""
    try:
        # Ler a aba dre_n2
        df_estrutura_n2 = pd.read_excel(filename, sheet_name="dre_n2")
        
        if df_estrutura_n2.empty:
            print("⚠️ Aba dre_n2 está vazia")
            return []
        
        # Verificar se as colunas necessárias existem
        if "dre_n2" not in df_estrutura_n2.columns or "dre_n1" not in df_estrutura_n2.columns:
            print("⚠️ Colunas dre_n2 ou dre_n1 não encontradas na aba dre_n2")
            return []
        
        # Carregar estrutura dre_n1 para ordenação
        df_estrutura_n1 = pd.read_excel(filename, sheet_name="dre_n1")
        
        # Criar mapeamento de dre_n1 para dre_n1_id
        mapeamento_n1 = {}
        for _, row in df_estrutura_n1.iterrows():
            dre_n1 = str(row.get('dre_n1', ''))
            dre_n1_id = row.get('dre_n1_id', 0)
            if dre_n1 and dre_n1 != 'nan':
                mapeamento_n1[dre_n1] = dre_n1_id
        
        estrutura = []
        for _, row in df_estrutura_n2.iterrows():
            dre_n2 = row["dre_n2"]
            dre_n1 = row["dre_n1"]
            dre_n2_id = row.get('dre_n2_id', 0)
            
            if pd.notna(dre_n2) and str(dre_n2).strip():
                nome = extrair_nome_conta(str(dre_n2))
                tipo = extrair_tipo_operacao(str(dre_n2))
                totalizador = extrair_nome_conta(str(dre_n1)) if pd.notna(dre_n1) and str(dre_n1).strip() else ""
                
                estrutura.append({
                    "nome": nome,
                    "tipo": tipo,
                    "totalizador": totalizador,
                    "dre_n2_id": dre_n2_id,
                    "dre_n1_id": mapeamento_n1.get(str(dre_n1), 0)
                })
        
        # Ordenar por dre_n1_id primeiro, depois por dre_n2_id
        estrutura.sort(key=lambda x: (x["dre_n1_id"], x["dre_n2_id"]))
        
        return estrutura
        
    except Exception as e:
        print(f"❌ Erro ao carregar estrutura DRE: {e}")
        return [] 

def carregar_estrutura_dre_simplificada(filename="financial-data-roriz.xlsx"):
    """Carrega a estrutura DRE da aba 'dre' com estrutura simplificada"""
    try:
        # Ler a aba dre
        df_estrutura = pd.read_excel(filename, sheet_name="dre")
        
        if df_estrutura.empty:
            print("⚠️ Aba dre está vazia")
            return []
        
        # Verificar se as colunas necessárias existem
        if "dre" not in df_estrutura.columns or "dre_id" not in df_estrutura.columns:
            print("⚠️ Colunas dre ou dre_id não encontradas na aba dre")
            return []
        
        estrutura = []
        for _, row in df_estrutura.iterrows():
            dre = str(row.get('dre', ''))
            dre_id = row.get('dre_id', 0)
            
            if pd.notna(dre) and str(dre).strip():
                nome = extrair_nome_conta(str(dre))
                tipo = extrair_tipo_operacao(str(dre))
                
                estrutura.append({
                    "nome": nome,
                    "tipo": tipo,
                    "dre_id": dre_id,
                    "totalizador": nome,  # Cada item é seu próprio totalizador
                    "expandivel": tipo != "="  # Só itens que não são "=" são expansíveis
                })
        
        # Ordenar por dre_id
        estrutura.sort(key=lambda x: x["dre_id"])
        
        return estrutura
        
    except Exception as e:
        print(f"❌ Erro ao carregar estrutura DRE simplificada: {e}")
        return [] 