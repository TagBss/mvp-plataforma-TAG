"""
Helper para funções de debug e validação do DRE N0
"""
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.engine import Connection

class DebugHelper:
    """Helper para operações de debug e validação do DRE N0"""
    
    @staticmethod
    def check_table_structure(connection: Connection, table_name: str = "dre_structure_n0") -> Dict[str, Any]:
        """Verifica a estrutura de uma tabela"""
        try:
            # Verificar se a tabela existe
            check_table = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """)
            
            result = connection.execute(check_table, {"table_name": table_name})
            table_exists = result.scalar()
            
            if not table_exists:
                return {
                    "success": False,
                    "error": f"Tabela {table_name} não existe",
                    "tables": []
                }
            
            # Verificar estrutura da tabela
            structure_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            structure_result = connection.execute(structure_query, {"table_name": table_name})
            columns = [{"name": row.column_name, "type": row.data_type, "nullable": row.is_nullable} for row in structure_result]
            
            # Verificar dados da tabela
            data_query = text(f"SELECT COUNT(*) as total FROM {table_name} WHERE is_active = true")
            data_result = connection.execute(data_query)
            total_records = data_result.scalar()
            
            # Verificar alguns registros
            sample_query = text(f"SELECT id, name, operation_type, order_index FROM {table_name} WHERE is_active = true LIMIT 5")
            sample_result = connection.execute(sample_query)
            samples = [{"id": row.id, "name": row.name, "operation_type": row.operation_type, "order_index": row.order_index} for row in sample_result]
            
            return {
                "success": True,
                "table_exists": table_exists,
                "total_records": total_records,
                "columns": columns,
                "samples": samples
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": str(e.__traceback__)
            }
    
    @staticmethod
    def test_database_connection(connection: Connection) -> Dict[str, Any]:
        """Testa a conexão com o banco de dados"""
        try:
            # Query simples para testar conexão
            query = text("SELECT 1 as teste")
            result = connection.execute(query)
            row = result.fetchone()
            
            return {
                "success": True,
                "message": "Conexão com banco funcionando",
                "teste": row.teste if row else "N/A"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na conexão: {str(e)}"
            }
    
    @staticmethod
    def test_classificacoes_query(connection: Connection, dre_n2_name: str) -> Dict[str, Any]:
        """Testa a query de classificações"""
        try:
            # Query simples para testar
            query = text("""
                SELECT DISTINCT classificacao
                FROM financial_data 
                WHERE dre_n2 = :dre_n2_name
                AND classificacao IS NOT NULL 
                AND classificacao::text <> ''
                AND classificacao::text <> 'nan'
                ORDER BY classificacao
                LIMIT 5
            """)
            
            result = connection.execute(query, {"dre_n2_name": dre_n2_name})
            rows = result.fetchall()
            
            return {
                "success": True,
                "message": f"Query executada com sucesso para {dre_n2_name}",
                "total_rows": len(rows),
                "classificacoes": [row.classificacao for row in rows] if rows else []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na query: {str(e)}"
            }
    
    @staticmethod
    def get_database_info(connection: Connection) -> Dict[str, Any]:
        """Obtém informações gerais do banco de dados"""
        try:
            # Versão do PostgreSQL
            version_query = text("SELECT version()")
            version_result = connection.execute(version_query)
            version = version_result.scalar()
            
            # Tamanho do banco
            size_query = text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size_result = connection.execute(size_query)
            size = size_result.scalar()
            
            # Número de conexões ativas
            connections_query = text("""
                SELECT count(*) as active_connections 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            connections_result = connection.execute(connections_query)
            active_connections = connections_result.scalar()
            
            return {
                "success": True,
                "version": version,
                "database_size": size,
                "active_connections": active_connections,
                "current_database": connection.engine.url.database
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
