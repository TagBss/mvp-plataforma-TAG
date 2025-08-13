"""
Repository especializado para dados financeiros com base na estrutura real da financial_data
"""
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, or_
import pandas as pd

from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import (
    FinancialData, 
    DFCStructureN1, DFCStructureN2, DFCClassification,
    DREStructureN1, DREStructureN2, DREClassification
)

class SpecializedFinancialRepository:
    """Repository especializado para consultas específicas baseadas na estrutura real"""
    
    def get_dfc_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Busca dados DFC estruturados conforme a versão Excel"""
        
        with DatabaseSession() as session:
            # Buscar dados financeiros DFC
            query = session.query(FinancialData).filter(
                FinancialData.dfc_n1.isnot(None),
                FinancialData.dfc_n2.isnot(None)
            )
            
            if start_date:
                query = query.filter(FinancialData.data >= start_date)
            if end_date:
                query = query.filter(FinancialData.data <= end_date)
            
            financial_data = query.all()
            
            if not financial_data:
                return self._empty_dfc_response()
            
            # Converter para DataFrame para processamento
            df = pd.DataFrame([{
                'id': item.id,
                'nome': item.nome,
                'classificacao': item.classificacao,
                'data': item.data,
                'valor': float(item.valor) if item.valor else 0.0,
                'dfc_n1': item.dfc_n1,
                'dfc_n2': item.dfc_n2,
                'origem': item.origem
            } for item in financial_data])
            
            # Processar períodos
            df['data'] = pd.to_datetime(df['data'])
            df['mes'] = df['data'].dt.strftime('%Y-%m')
            df['ano'] = df['data'].dt.year
            df['trimestre'] = df['data'].dt.to_period('Q').astype(str)
            
            meses = sorted(df['mes'].unique())
            anos = sorted(df['ano'].unique())
            trimestres = sorted(df['trimestre'].unique())
            
            # Separar realizado e orçamento
            df_real = df[df['origem'] != 'ORC'].copy()
            df_orc = df[df['origem'] == 'ORC'].copy()
            
            # Buscar estruturas DFC do banco
            dfc_structures = session.query(DFCStructureN1).options(
                joinedload(DFCStructureN1.children).joinedload(DFCStructureN2.classifications)
            ).order_by(DFCStructureN1.order_index).all()
            
            # Construir resposta estruturada
            result = []
            
            # 1. Saldo inicial
            saldo_inicial = self._create_dfc_item("Saldo inicial", "=", meses, trimestres, anos)
            result.append(saldo_inicial)
            
            # 2. Movimentações
            movimentacoes = self._create_dfc_item("Movimentações", "=", meses, trimestres, anos)
            movimentacoes["classificacoes"] = []
            
            # Processar cada estrutura DFC N1
            for dfc_n1 in dfc_structures:
                totalizador = self._create_dfc_item(dfc_n1.name, dfc_n1.operation_type, meses, trimestres, anos)
                totalizador["classificacoes"] = []
                
                # Processar cada DFC N2 do totalizador
                for dfc_n2 in dfc_n1.children:
                    conta_item = self._create_dfc_item(dfc_n2.name, dfc_n2.operation_type, meses, trimestres, anos)
                    conta_item["classificacoes"] = []
                    
                    # Buscar dados que correspondem a este DFC N2
                    df_conta = self._match_dfc_data(df_real, dfc_n1.name, dfc_n2.name)
                    
                    if not df_conta.empty:
                        # Calcular valores por período
                        self._calculate_periods(conta_item, df_conta, meses, trimestres, anos, dfc_n2.operation_type)
                        
                        # Processar classificações
                        for classification in dfc_n2.classifications:
                            df_class = df_conta[df_conta['classificacao'] == classification.name]
                            if not df_class.empty:
                                class_item = self._create_dfc_item(classification.name, dfc_n2.operation_type, meses, trimestres, anos)
                                self._calculate_periods(class_item, df_class, meses, trimestres, anos, dfc_n2.operation_type)
                                conta_item["classificacoes"].append(class_item)
                        
                        # Adicionar conta ao totalizador
                        totalizador["classificacoes"].append(conta_item)
                        
                        # Somar ao totalizador
                        self._sum_to_parent(totalizador, conta_item, meses, trimestres, anos)
                
                # Adicionar totalizador às movimentações
                movimentacoes["classificacoes"].append(totalizador)
                self._sum_to_parent(movimentacoes, totalizador, meses, trimestres, anos)
            
            result.append(movimentacoes)
            
            # 3. Saldo final
            saldo_final = self._create_dfc_item("Saldo final", "=", meses, trimestres, anos)
            saldo_final["valores_mensais"] = movimentacoes["valores_mensais"].copy()
            saldo_final["valores_trimestrais"] = movimentacoes["valores_trimestrais"].copy()
            saldo_final["valores_anuais"] = movimentacoes["valores_anuais"].copy()
            saldo_final["valor"] = movimentacoes["valor"]
            result.append(saldo_final)
            
            return {
                "success": True,
                "meses": meses,
                "trimestres": trimestres,
                "anos": [str(ano) for ano in anos],
                "data": result
            }
    
    def get_dre_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Busca dados DRE estruturados conforme a versão Excel"""
        
        with DatabaseSession() as session:
            # Buscar dados financeiros DRE
            query = session.query(FinancialData).filter(
                FinancialData.dre_n1.isnot(None),
                FinancialData.dre_n2.isnot(None)
            )
            
            if start_date:
                query = query.filter(FinancialData.competencia >= start_date)
            if end_date:
                query = query.filter(FinancialData.competencia <= end_date)
            
            financial_data = query.all()
            
            if not financial_data:
                return self._empty_dre_response()
            
            # Converter para DataFrame para processamento
            df = pd.DataFrame([{
                'id': item.id,
                'nome': item.nome,
                'classificacao': item.classificacao,
                'competencia': item.competencia,
                'valor_original': float(item.valor_original) if item.valor_original else 0.0,
                'dre_n1': item.dre_n1,
                'dre_n2': item.dre_n2,
                'origem': item.origem
            } for item in financial_data])
            
            # Processar períodos
            df['competencia'] = pd.to_datetime(df['competencia'])
            df['mes'] = df['competencia'].dt.strftime('%Y-%m')
            df['ano'] = df['competencia'].dt.year
            df['trimestre'] = df['competencia'].dt.to_period('Q').astype(str)
            
            meses = sorted(df['mes'].unique())
            anos = sorted(df['ano'].unique())
            trimestres = sorted(df['trimestre'].unique())
            
            # Separar realizado e orçamento
            df_real = df[df['origem'] != 'ORC'].copy()
            df_orc = df[df['origem'] == 'ORC'].copy()
            
            # Buscar estruturas DRE do banco
            dre_structures = session.query(DREStructureN1).options(
                joinedload(DREStructureN1.children).joinedload(DREStructureN2.classifications)
            ).order_by(DREStructureN1.order_index).all()
            
            # Construir resposta estruturada
            result = []
            
            # Processar cada estrutura DRE N1
            for dre_n1 in dre_structures:
                totalizador = self._create_dre_item(dre_n1.name, dre_n1.operation_type, meses, trimestres, anos)
                totalizador["classificacoes"] = []
                
                # Processar cada DRE N2 do totalizador
                for dre_n2 in dre_n1.children:
                    conta_item = self._create_dre_item(dre_n2.name, dre_n2.operation_type, meses, trimestres, anos)
                    conta_item["classificacoes"] = []
                    
                    # Buscar dados que correspondem a este DRE N2
                    df_conta = self._match_dre_data(df_real, dre_n1.name, dre_n2.name)
                    
                    if not df_conta.empty:
                        # Calcular valores por período
                        self._calculate_dre_periods(conta_item, df_conta, meses, trimestres, anos, dre_n2.operation_type)
                        
                        # Processar classificações
                        for classification in dre_n2.classifications:
                            df_class = df_conta[df_conta['classificacao'] == classification.name]
                            if not df_class.empty:
                                class_item = self._create_dre_item(classification.name, dre_n2.operation_type, meses, trimestres, anos)
                                self._calculate_dre_periods(class_item, df_class, meses, trimestres, anos, dre_n2.operation_type)
                                conta_item["classificacoes"].append(class_item)
                        
                        # Adicionar conta ao totalizador
                        totalizador["classificacoes"].append(conta_item)
                        
                        # Somar ao totalizador
                        self._sum_to_parent(totalizador, conta_item, meses, trimestres, anos)
                
                result.append(totalizador)
            
            return {
                "success": True,
                "meses": meses,
                "trimestres": trimestres,
                "anos": [str(ano) for ano in anos],
                "data": result
            }
    
    def get_receber_data(
        self,
        mes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Busca dados de contas a receber baseado na origem CAR (como na versão Excel)"""
        
        with DatabaseSession() as session:
            # Filtrar por origem CAR (Contas a Receber)
            query = session.query(FinancialData).filter(
                FinancialData.origem == 'CAR'
            )
            
            if mes:
                # Filtrar por mês específico usando a data principal
                year, month = map(int, mes.split('-'))
                query = query.filter(
                    func.extract('year', FinancialData.data) == year,
                    func.extract('month', FinancialData.data) == month
                )
            
            data = query.all()
            
            if not data:
                return {"success": True, "data": {"saldo_total": 0, "mom_analysis": [], "meses_disponiveis": [], "pmr": "30 dias"}}
            
            # Calcular saldo total
            saldo_total = sum(float(item.valor) if item.valor else 0.0 for item in data)
            
            # Calcular meses disponíveis
            meses_disponiveis = sorted(list(set(
                item.data.strftime('%Y-%m') for item in data if item.data
            )))
            
            return {
                "success": True,
                "data": {
                    "saldo_total": round(saldo_total, 2),
                    "mom_analysis": self._calculate_mom_analysis(data, "receber"),
                    "meses_disponiveis": meses_disponiveis,
                    "pmr": "30 dias"  # Prazo médio de recebimento
                }
            }
    
    def get_pagar_data(
        self,
        mes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Busca dados de contas a pagar baseado na origem CAP (como na versão Excel)"""
        
        with DatabaseSession() as session:
            # Filtrar por origem CAP (Contas a Pagar)
            query = session.query(FinancialData).filter(
                FinancialData.origem == 'CAP'
            )
            
            if mes:
                # Filtrar por mês específico usando a data principal
                year, month = map(int, mes.split('-'))
                query = query.filter(
                    func.extract('year', FinancialData.data) == year,
                    func.extract('month', FinancialData.data) == month
                )
            
            data = query.all()
            
            if not data:
                return {"success": True, "data": {"saldo_total": 0, "mom_analysis": [], "meses_disponiveis": [], "pmp": "30 dias"}}
            
            # Calcular saldo total (valor absoluto para pagar)
            saldo_total = abs(sum(float(item.valor) if item.valor else 0.0 for item in data))
            
            # Calcular meses disponíveis
            meses_disponiveis = sorted(list(set(
                item.data.strftime('%Y-%m') for item in data if item.data
            )))
            
            return {
                "success": True,
                "data": {
                    "saldo_total": round(saldo_total, 2),
                    "mom_analysis": self._calculate_mom_analysis(data, "pagar"),
                    "meses_disponiveis": meses_disponiveis,
                    "pmp": "30 dias"  # Prazo médio de pagamento
                }
            }
    
    # === MÉTODOS AUXILIARES ===
    
    def _empty_dfc_response(self):
        return {"success": True, "meses": [], "trimestres": [], "anos": [], "data": []}
    
    def _empty_dre_response(self):
        return {"success": True, "meses": [], "trimestres": [], "anos": [], "data": []}
    
    def _create_dfc_item(self, name: str, operation_type: str, meses: List[str], trimestres: List[str], anos: List[int]):
        return {
            "nome": name,
            "tipo": operation_type,
            "valor": 0.0,
            "valores_mensais": {mes: 0.0 for mes in meses},
            "valores_trimestrais": {tri: 0.0 for tri in trimestres},
            "valores_anuais": {str(ano): 0.0 for ano in anos},
            "horizontal_mensais": {mes: "–" for mes in meses},
            "horizontal_trimestrais": {tri: "–" for tri in trimestres},
            "horizontal_anuais": {str(ano): "–" for ano in anos}
        }
    
    def _create_dre_item(self, name: str, operation_type: str, meses: List[str], trimestres: List[str], anos: List[int]):
        return {
            "nome": name,
            "tipo": operation_type,
            "valor": 0.0,
            "valores_mensais": {mes: 0.0 for mes in meses},
            "valores_trimestrais": {tri: 0.0 for tri in trimestres},
            "valores_anuais": {str(ano): 0.0 for ano in anos},
            "orcamentos_mensais": {mes: 0.0 for mes in meses},
            "orcamentos_trimestrais": {tri: 0.0 for tri in trimestres},
            "orcamentos_anuais": {str(ano): 0.0 for ano in anos},
            "horizontal_mensais": {mes: "–" for mes in meses},
            "horizontal_trimestrais": {tri: "–" for tri in trimestres},
            "horizontal_anuais": {str(ano): "–" for ano in anos}
        }
    
    def _match_dfc_data(self, df: pd.DataFrame, dfc_n1_name: str, dfc_n2_name: str) -> pd.DataFrame:
        """Encontra dados que correspondem aos nomes DFC N1 e N2 baseado na estrutura Excel"""
        from helpers.structure_helper import extrair_nome_conta
        
        # Extrair nomes limpos dos dados
        df_copy = df.copy()
        df_copy['dfc_n1_clean'] = df_copy['dfc_n1'].apply(lambda x: extrair_nome_conta(str(x)) if x else '')
        df_copy['dfc_n2_clean'] = df_copy['dfc_n2'].apply(lambda x: extrair_nome_conta(str(x)) if x else '')
        
        # Match exato com nomes limpos
        return df_copy[
            (df_copy['dfc_n1_clean'].str.lower() == dfc_n1_name.lower()) &
            (df_copy['dfc_n2_clean'].str.lower() == dfc_n2_name.lower())
        ]
    
    def _match_dre_data(self, df: pd.DataFrame, dre_n1_name: str, dre_n2_name: str) -> pd.DataFrame:
        """Encontra dados que correspondem aos nomes DRE N1 e N2 baseado na estrutura Excel"""
        from helpers.structure_helper import extrair_nome_conta
        
        # Extrair nomes limpos dos dados
        df_copy = df.copy()
        df_copy['dre_n1_clean'] = df_copy['dre_n1'].apply(lambda x: extrair_nome_conta(str(x)) if x else '')
        df_copy['dre_n2_clean'] = df_copy['dre_n2'].apply(lambda x: extrair_nome_conta(str(x)) if x else '')
        
        # Match exato com nomes limpos
        return df_copy[
            (df_copy['dre_n1_clean'].str.lower() == dre_n1_name.lower()) &
            (df_copy['dre_n2_clean'].str.lower() == dre_n2_name.lower())
        ]
    
    def _calculate_periods(self, item: Dict, df: pd.DataFrame, meses: List[str], trimestres: List[str], anos: List[int], operation_type: str):
        """Calcula valores por período para DFC seguindo a lógica Excel"""
        for mes in meses:
            df_mes = df[df['mes'] == mes]
            valor = float(df_mes['valor'].sum())
            
            # Aplicar operação conforme a estrutura Excel
            if operation_type == '-':
                valor = -abs(valor)  # Forçar negativo
            elif operation_type == '+':
                valor = abs(valor)   # Forçar positivo
            elif operation_type == '+/-':
                valor = valor        # Manter sinal original
            # Para '=', manter valor como está
            
            item["valores_mensais"][mes] = valor
        
        for tri in trimestres:
            df_tri = df[df['trimestre'] == tri]
            valor = float(df_tri['valor'].sum())
            
            if operation_type == '-':
                valor = -abs(valor)
            elif operation_type == '+':
                valor = abs(valor)
            elif operation_type == '+/-':
                valor = valor
            
            item["valores_trimestrais"][tri] = valor
        
        for ano in anos:
            df_ano = df[df['ano'] == ano]
            valor = float(df_ano['valor'].sum())
            
            if operation_type == '-':
                valor = -abs(valor)
            elif operation_type == '+':
                valor = abs(valor)
            elif operation_type == '+/-':
                valor = valor
            
            item["valores_anuais"][str(ano)] = valor
        
        item["valor"] = float(sum(item["valores_mensais"].values()))
    
    def _calculate_dre_periods(self, item: Dict, df: pd.DataFrame, meses: List[str], trimestres: List[str], anos: List[int], operation_type: str):
        """Calcula valores por período para DRE seguindo a lógica Excel"""
        for mes in meses:
            df_mes = df[df['mes'] == mes]
            valor = float(df_mes['valor_original'].sum())
            
            # Aplicar operação conforme a estrutura Excel
            if operation_type == '-':
                valor = -abs(valor)  # Forçar negativo
            elif operation_type == '+':
                valor = abs(valor)   # Forçar positivo
            elif operation_type == '+/-':
                valor = valor        # Manter sinal original
            # Para '=', manter valor como está
            
            item["valores_mensais"][mes] = valor
            item["orcamentos_mensais"][mes] = 0.0  # TODO: implementar orçamentos
        
        for tri in trimestres:
            df_tri = df[df['trimestre'] == tri]
            valor = float(df_tri['valor_original'].sum())
            
            if operation_type == '-':
                valor = -abs(valor)
            elif operation_type == '+':
                valor = abs(valor)
            elif operation_type == '+/-':
                valor = valor
            
            item["valores_trimestrais"][tri] = valor
            item["orcamentos_trimestrais"][tri] = 0.0
        
        for ano in anos:
            df_ano = df[df['ano'] == ano]
            valor = float(df_ano['valor_original'].sum())
            
            if operation_type == '-':
                valor = -abs(valor)
            elif operation_type == '+':
                valor = abs(valor)
            elif operation_type == '+/-':
                valor = valor
            
            item["valores_anuais"][str(ano)] = valor
            item["orcamentos_anuais"][str(ano)] = 0.0
        
        item["valor"] = float(sum(item["valores_mensais"].values()))
        item["orcamento_total"] = 0.0
    
    def _sum_to_parent(self, parent: Dict, child: Dict, meses: List[str], trimestres: List[str], anos: List[int]):
        """Soma valores do filho ao pai"""
        for mes in meses:
            parent["valores_mensais"][mes] += child["valores_mensais"][mes]
        
        for tri in trimestres:
            parent["valores_trimestrais"][tri] += child["valores_trimestrais"][tri]
        
        for ano in anos:
            parent["valores_anuais"][str(ano)] += child["valores_anuais"][str(ano)]
        
        parent["valor"] += child["valor"]
    
    def _calculate_mom_analysis(self, data: List, tipo: str) -> List[Dict]:
        """Calcula análise Month-over-Month usando a coluna data"""
        if not data:
            return []
        
        # Agrupar por mês usando a coluna data
        df = pd.DataFrame([{
            'mes': item.data.strftime('%Y-%m') if item.data else '',
            'valor': float(item.valor) if item.valor else 0.0
        } for item in data if item.data])
        
        if df.empty:
            return []
        
        monthly_totals = df.groupby('mes')['valor'].sum().reset_index()
        monthly_totals = monthly_totals.sort_values('mes')
        
        mom_data = []
        for i, row in monthly_totals.iterrows():
            mes = row['mes']
            valor_atual = row['valor']
            valor_anterior = monthly_totals.iloc[i-1]['valor'] if i > 0 else None
            
            variacao_absoluta = None
            variacao_percentual = None
            
            if valor_anterior is not None:
                variacao_absoluta = valor_atual - valor_anterior
                if valor_anterior != 0:
                    variacao_percentual = (variacao_absoluta / valor_anterior) * 100
            
            mom_data.append({
                "mes": mes,
                "valor_atual": valor_atual,
                "valor_anterior": valor_anterior,
                "variacao_absoluta": variacao_absoluta,
                "variacao_percentual": variacao_percentual
            })
        
        return mom_data
