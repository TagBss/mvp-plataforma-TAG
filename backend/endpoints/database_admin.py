"""
Endpoint para visualização de dados do banco via navegador
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from database.connection_sqlalchemy import get_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import pandas as pd

router = APIRouter(prefix="/admin", tags=["database-admin"])

@router.get("/database", response_class=HTMLResponse)
async def view_database():
    """Interface web para visualizar dados do banco"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Listar apenas tabelas e views atuais (excluindo backups)
        tables_query = """
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type IN ('BASE TABLE', 'VIEW')
        AND table_name NOT LIKE '%_backup_%'
        AND table_name NOT LIKE 'backup_summary_%'
        ORDER BY table_type DESC, table_name;
        """
        
        tables_result = session.execute(text(tables_query)).fetchall()
        
        # Contar registros de cada tabela e view
        table_info = []
        for row in tables_result:
            table_name = row[0]
            table_type = "table" if row[1] == "BASE TABLE" else "view"
            try:
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = session.execute(text(count_query)).scalar()
                table_info.append({"name": table_name, "count": count, "type": table_type})
            except Exception as e:
                table_info.append({"name": table_name, "count": f"Erro: {e}", "type": table_type})
        
        session.close()
        
        # Gerar HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Admin - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: #2c3e50; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }}
                .table-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                }}
                .table-card {{ 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    padding: 15px; 
                    background: #f9f9f9;
                    transition: transform 0.2s;
                }}
                .table-card:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                .table-name {{ 
                    font-weight: bold; 
                    color: #2c3e50; 
                    font-size: 18px;
                    margin-bottom: 10px;
                }}
                .table-count {{ 
                    color: #27ae60; 
                    font-size: 24px; 
                    font-weight: bold;
                }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 8px 15px; 
                    text-decoration: none; 
                    border-radius: 3px; 
                    margin: 5px;
                    display: inline-block;
                }}
                .btn:hover {{ background: #2980b9; }}
                .links {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🗄️ Database Admin - TAG Financeiro</h1>
                    <p>Banco: <strong>tag_financeiro</strong> | Host: <strong>localhost:5432</strong></p>
                </div>
                
                <h2>📊 Tabelas e Views Ativas do Sistema</h2>
                <p style="color: #666; margin-bottom: 20px;">
                    <span style="color: #2c3e50;">📋 Tabelas</span> | 
                    <span style="color: #e74c3c;">👁️ Views SQL</span>
                    <br><small style="color: #95a5a6;">💡 Apenas tabelas e views em uso ativo (backups não incluídos)</small>
                </p>
                <div class="table-grid">
        """
        
        for item in table_info:
            # Ícone e cor baseado no tipo
            if item['type'] == 'view':
                icon = "👁️"
                color = "#e74c3c"
                structure_link = ""
            else:
                icon = "📋"
                color = "#2c3e50"
                structure_link = f'<a href="/admin/table/{item["name"]}/structure" class="btn">Estrutura</a>'
            
            html_content += f"""
                    <div class="table-card">
                        <div class="table-name" style="color: {color};">{icon} {item['name']}</div>
                        <div class="table-count">{item['count']} registros</div>
                        <div style="margin-top: 10px;">
                            <a href="/admin/table/{item['name']}" class="btn">Ver Dados</a>
                            {structure_link}
                        </div>
                    </div>
            """
        
        html_content += f"""
                </div>
                
                <div class="links">
                    <h3>🔗 Links Úteis</h3>
                    <a href="/docs" class="btn">📚 API Docs</a>
                    <a href="/financial-data/dfc" class="btn">📊 DFC PostgreSQL</a>
                    <a href="/dfc" class="btn">📈 DFC Excel</a>
                </div>
                
                <div class="links" style="margin-top: 20px;">
                    <h3>🚀 Executar Views SQL</h3>
                    <a href="/admin/debug-views" class="btn" style="background: #9b59b6;">🔍 Debug Views</a>
                    <a href="/admin/create-simple-view" class="btn" style="background: #f39c12;">🧪 Criar View Simples</a>
                    <a href="/admin/execute-views" class="btn" style="background: #e74c3c;">📋 Criar Views DRE/DFC</a>
                    <a href="/admin/test-views" class="btn" style="background: #27ae60;">🧪 Testar Views</a>
                </div>
                
                <div class="links" style="margin-top: 20px;">
                    <h3>💾 Sistema de Backups</h3>
                    <a href="/admin/backups" class="btn" style="background: #16a085;">📦 Gerenciar Backups</a>
                    <a href="/admin/create-backup" class="btn" style="background: #e67e22;">🔄 Criar Novo Backup</a>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>📊 <strong>Tabelas ativas:</strong> {len([t for t in table_info if t['type'] == 'table'])} | <strong>Views ativas:</strong> {len([t for t in table_info if t['type'] == 'view'])} | <strong>Atualizado:</strong> {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <p style="color: #95a5a6; font-size: 14px;">💾 Para ver backups, use a seção "Sistema de Backups" abaixo</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro de Conexão</h1>
            <p>Não foi possível conectar ao banco de dados:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/docs">← Voltar para API Docs</a></p>
        </body>
        </html>
        """

@router.get("/execute-views", response_class=HTMLResponse)
async def execute_views():
    """Executar as views SQL para DRE, DFC e Receber/Pagar"""
    
    try:
        engine = get_engine()
        
        # Usar conexão direta para evitar problemas de transação
        with engine.connect() as connection:
            # Ler e executar os arquivos SQL
            views_files = [
                ("views_simples.sql", "Views Simples"),
                ("views_dre.sql", "DRE"),
                ("views_dfc.sql", "DFC"), 
                ("views_receber_pagar.sql", "Receber/Pagar")
            ]
            
            results = []
            for filename, description in views_files:
                try:
                    file_path = f"database/{filename}"
                    print(f"📁 Lendo arquivo: {file_path}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    print(f"📄 Conteúdo do arquivo {filename}: {len(sql_content)} caracteres")
                    
                    # Executar cada comando SQL separadamente
                    commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
                    print(f"🔧 Comandos encontrados: {len(commands)}")
                    
                    for i, cmd in enumerate(commands):
                        if cmd and not cmd.startswith('--') and not cmd.startswith('/*'):
                            try:
                                print(f"   Executando comando {i+1}: {cmd[:100]}...")
                                connection.execute(text(cmd))
                                connection.commit()
                                print(f"   ✅ Comando {i+1} executado com sucesso")
                            except Exception as cmd_error:
                                print(f"   ❌ Erro no comando {i+1}: {str(cmd_error)}")
                                connection.rollback()
                                raise cmd_error
                    
                    results.append({"name": description, "status": "✅ Sucesso", "message": f"Views {description} criadas"})
                    print(f"✅ {description} - Views criadas com sucesso")
                    
                except Exception as e:
                    print(f"❌ Erro em {description}: {str(e)}")
                    results.append({"name": description, "status": "❌ Erro", "message": str(e)})
        
        # Gerar HTML de resultado
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Executar Views SQL - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .result-item {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }}
                .success {{ border-left: 5px solid #27ae60; }}
                .error {{ border-left: 5px solid #e74c3c; }}
                .btn {{ background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; margin: 5px; display: inline-block; }}
                .sql-preview {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin: 10px 0; font-family: monospace; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Execução de Views SQL</h1>
                    <p>Resultado da criação das views DRE, DFC e Receber/Pagar</p>
                </div>
                
                <h2>📊 Resultados da Execução</h2>
        """
        
        for result in results:
            css_class = "success" if "Sucesso" in result["status"] else "error"
            html_content += f"""
                <div class="result-item {css_class}">
                    <h3>{result['name']}</h3>
                    <p><strong>Status:</strong> {result['status']}</p>
                    <p><strong>Mensagem:</strong> {result['message']}</p>
                </div>
            """
        
        html_content += f"""
                <div style="margin-top: 30px; text-align: center;">
                    <a href="/admin/database" class="btn">← Voltar ao Admin</a>
                    <a href="/admin/test-views" class="btn" style="background: #27ae60;">🧪 Testar Views</a>
                </div>
                
                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
                    <h3>📋 Comandos SQL Executados</h3>
                    <p>As seguintes views foram criadas:</p>
                    <ul>
                        <li><strong>Views Simples:</strong> v_dre_simples, v_dfc_simples, v_receber_simples, v_pagar_simples</li>
                        <li><strong>DRE:</strong> v_dre_completo, v_dre_resumida, v_dre_por_periodo</li>
                        <li><strong>DFC:</strong> v_dfc_completo, v_dfc_resumida, v_dfc_por_periodo, v_dfc_saldo_acumulado</li>
                        <li><strong>Receber/Pagar:</strong> v_contas_receber, v_contas_pagar, v_resumo_receber_pagar</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        print(f"❌ Erro geral na execução: {str(e)}")
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro na Execução</h1>
            <p>Erro ao executar as views:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/create-simple-view", response_class=HTMLResponse)
async def create_simple_view():
    """Criar uma view simples para teste"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Criar uma view muito simples
            simple_view_sql = """
            CREATE OR REPLACE VIEW v_teste_simples AS
            SELECT 
                dre_n2,
                COUNT(*) as total_registros,
                SUM(valor_original) as valor_total
            FROM financial_data 
            WHERE dre_n2 IS NOT NULL 
            AND dre_n2 != '' 
            AND dre_n2 != 'nan'
            GROUP BY dre_n2
            LIMIT 10;
            """
            
            try:
                print("🔧 Criando view de teste...")
                connection.execute(text(simple_view_sql))
                connection.commit()
                print("✅ View de teste criada com sucesso")
                
                # Testar se a view foi criada
                test_query = "SELECT COUNT(*) FROM v_teste_simples"
                result = connection.execute(text(test_query)).scalar()
                result = result if result is not None else 0
                print(f"✅ View testada: {result} registros")
                
                return f"""
                <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h1>✅ View de Teste Criada!</h1>
                    <p>A view <strong>v_teste_simples</strong> foi criada com sucesso!</p>
                    <p><strong>Registros encontrados:</strong> {result}</p>
                    
                    <h2>🔧 Próximos Passos:</h2>
                    <ol>
                        <li>Teste esta view: <a href="/admin/test-simple-view">🧪 Testar View Simples</a></li>
                        <li>Crie as views completas: <a href="/admin/execute-views">📋 Criar Views Completas</a></li>
                        <li>Volte ao admin: <a href="/admin/database">🏠 Admin Principal</a></li>
                    </ol>
                    
                    <h3>📊 SQL Executado:</h3>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px;">{simple_view_sql}</pre>
                    
                    <h3>🧪 Teste Rápido:</h3>
                    <p>Teste esta consulta SQL diretamente:</p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 12px;">SELECT * FROM v_teste_simples LIMIT 5;</pre>
                </body>
                </html>
                """
                
            except Exception as e:
                print(f"❌ Erro ao criar view: {str(e)}")
                connection.rollback()
                return f"""
                <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h1>❌ Erro ao Criar View</h1>
                    <p>Erro ao criar a view de teste:</p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
                    <p><a href="/admin/database">← Voltar ao Admin</a></p>
                </body>
                </html>
                """
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro de Conexão</h1>
            <p>Erro ao conectar ao banco:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/test-simple-view", response_class=HTMLResponse)
async def test_simple_view():
    """Testar a view simples criada"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Testar a view
            test_query = "SELECT * FROM v_teste_simples LIMIT 5"
            result = connection.execute(text(test_query))
            rows = result.fetchall()
            
            # Gerar HTML com os resultados
            html_content = f"""
            <html>
            <head>
                <title>Teste View Simples - TAG Financeiro</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: #27ae60; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .btn {{ background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; margin: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🧪 Teste da View Simples</h1>
                        <p>View: <strong>v_teste_simples</strong></p>
                    </div>
                    
                    <h2>📊 Dados da View</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>DRE N2</th>
                                <th>Total Registros</th>
                                <th>Valor Total</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for row in rows:
                # Tratar valores None para evitar erros de formatação
                dre_n2 = row[0] if row[0] is not None else 'N/A'
                total_registros = row[1] if row[1] is not None else 0
                valor_total = row[2] if row[2] is not None else 0.0
                
                html_content += f"""
                            <tr>
                                <td>{dre_n2}</td>
                                <td>{total_registros}</td>
                                <td>R$ {valor_total:,.2f}</td>
                            </tr>
                """
            
            html_content += f"""
                        </tbody>
                    </table>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="/admin/database" class="btn">🏠 Admin Principal</a>
                        <a href="/admin/create-simple-view" class="btn" style="background: #e74c3c;">🔄 Recriar View</a>
                        <a href="/admin/execute-views" class="btn" style="background: #27ae60;">📋 Criar Views Completas</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro no Teste</h1>
            <p>Erro ao testar a view:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/test-views", response_class=HTMLResponse)
async def test_views():
    """Testar as views criadas"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Testar cada view
        test_queries = [
            # Views simples primeiro
            ("v_dre_simples", "SELECT COUNT(*) FROM v_dre_simples"),
            ("v_dfc_simples", "SELECT COUNT(*) FROM v_dfc_simples"),
            ("v_receber_simples", "SELECT COUNT(*) FROM v_receber_simples"),
            ("v_pagar_simples", "SELECT COUNT(*) FROM v_pagar_simples"),
            # Views complexas
            ("v_dre_completo", "SELECT COUNT(*) FROM v_dre_completo"),
            ("v_dre_resumida", "SELECT COUNT(*) FROM v_dre_resumida"),
            ("v_dre_por_periodo", "SELECT COUNT(*) FROM v_dre_por_periodo"),
            ("v_dfc_completo", "SELECT COUNT(*) FROM v_dfc_completo"),
            ("v_dfc_resumida", "SELECT COUNT(*) FROM v_dfc_resumida"),
            ("v_dfc_por_periodo", "SELECT COUNT(*) FROM v_dfc_por_periodo"),
            ("v_dfc_saldo_acumulado", "SELECT COUNT(*) FROM v_dfc_saldo_acumulado"),
            ("v_contas_receber", "SELECT COUNT(*) FROM v_contas_receber"),
            ("v_contas_pagar", "SELECT COUNT(*) FROM v_contas_pagar"),
            ("v_resumo_receber_pagar", "SELECT COUNT(*) FROM v_resumo_receber_pagar")
        ]
        
        test_results = []
        for view_name, query in test_queries:
            try:
                # Criar nova sessão para cada teste
                test_session = Session()
                result = test_session.execute(text(query)).scalar()
                test_results.append({"name": view_name, "status": "✅ OK", "count": result})
                test_session.close()
            except Exception as e:
                test_results.append({"name": view_name, "status": "❌ Erro", "count": f"Erro: {str(e)}"})
                try:
                    test_session.close()
                except:
                    pass
        
        session.close()
        
        # Gerar HTML de resultado
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Testar Views - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .result-item {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }}
                .success {{ border-left: 5px solid #27ae60; }}
                .error {{ border-left: 5px solid #e74c3c; }}
                .btn {{ background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; margin: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Teste de Views SQL</h1>
                    <p>Verificação das views DRE, DFC e Receber/Pagar</p>
                </div>
                
                <h2>📊 Resultados dos Testes</h2>
        """
        
        for result in test_results:
            css_class = "success" if "OK" in result["status"] else "error"
            html_content += f"""
                <div class="result-item {css_class}">
                    <h3>{result['name']}</h3>
                    <p><strong>Status:</strong> {result['status']}</p>
                    <p><strong>Registros:</strong> {result['count']}</p>
                </div>
            """
        
        html_content += f"""
                <div style="margin-top: 30px; text-align: center;">
                    <a href="/admin/database" class="btn">← Voltar ao Admin</a>
                    <a href="/admin/execute-views" class="btn" style="background: #e74c3c;">📋 Recriar Views</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro nos Testes</h1>
            <p>Erro ao testar as views:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/debug-views", response_class=HTMLResponse)
async def debug_views():
    """Debug das views existentes no banco"""
    
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            # Verificar se a view existe
            check_view_query = """
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname LIKE 'v_%'
            ORDER BY viewname;
            """
            
            views_result = connection.execute(text(check_view_query))
            views = [row[0] for row in views_result.fetchall()]
            
            # Verificar estrutura da tabela financial_data
            table_structure_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'financial_data'
            ORDER BY ordinal_position;
            """
            
            structure_result = connection.execute(text(table_structure_query))
            structure = [(row[0], row[1], row[2]) for row in structure_result.fetchall()]
            
            # Verificar dados de exemplo
            sample_data_query = """
            SELECT dre_n2, valor_original, competencia
            FROM financial_data 
            WHERE dre_n2 IS NOT NULL 
            AND dre_n2 != '' 
            AND dre_n2 != 'nan'
            LIMIT 5;
            """
            
            sample_result = connection.execute(text(sample_data_query))
            sample_data = [(row[0], row[1], row[2]) for row in sample_result.fetchall()]
            
            # Gerar HTML de debug
            html_content = f"""
            <html>
            <head>
                <title>Debug Views - TAG Financeiro</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .btn {{ background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; margin: 5px; display: inline-block; }}
                    .success {{ border-left: 5px solid #27ae60; }}
                    .warning {{ border-left: 5px solid #f39c12; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔍 Debug das Views</h1>
                        <p>Análise detalhada do estado das views no banco</p>
                    </div>
                    
                    <div class="section">
                        <h2>👁️ Views Existentes</h2>
                        <p><strong>Total de views encontradas:</strong> {len(views)}</p>
                        {f'<p><strong>Views:</strong> {", ".join(views)}</p>' if views else '<p style="color: #e74c3c;">❌ Nenhuma view encontrada!</p>'}
                    </div>
                    
                    <div class="section">
                        <h2>📋 Estrutura da Tabela Financial Data</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Coluna</th>
                                    <th>Tipo</th>
                                    <th>Pode ser Null</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for col_name, data_type, is_nullable in structure:
                html_content += f"""
                                <tr>
                                    <td>{col_name}</td>
                                    <td>{data_type}</td>
                                    <td>{is_nullable}</td>
                                </tr>
                """
            
            html_content += f"""
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>📊 Dados de Exemplo</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>DRE N2</th>
                                    <th>Valor Original</th>
                                    <th>Competência</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for dre_n2, valor, competencia in sample_data:
                html_content += f"""
                                <tr>
                                    <td>{dre_n2 if dre_n2 else 'N/A'}</td>
                                    <td>{valor if valor is not None else 'N/A'}</td>
                                    <td>{competencia if competencia else 'N/A'}</td>
                                </tr>
                """
            
            html_content += f"""
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>🔧 Ações Recomendadas</h2>
                        {f'<p style="color: #27ae60;">✅ Views existem. Teste-as: <a href="/admin/test-views" class="btn">🧪 Testar Views</a></p>' if views else '<p style="color: #e74c3c;">❌ Nenhuma view existe. Crie-as: <a href="/admin/create-simple-view" class="btn">🧪 Criar View Simples</a></p>'}
                    </div>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="/admin/database" class="btn">🏠 Admin Principal</a>
                        <a href="/admin/create-simple-view" class="btn" style="background: #f39c12;">🧪 Criar View Simples</a>
                        <a href="/admin/execute-views" class="btn" style="background: #e74c3c;">📋 Criar Views Completas</a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro no Debug</h1>
            <p>Erro ao fazer debug das views:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table_data(table_name: str, limit: int = 100):
    """Visualizar dados de uma tabela específica"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Para financial_data, usar ordem específica de colunas
        if table_name == 'financial_data':
            # Obter todas as colunas disponíveis
            columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'financial_data'
                ORDER BY ordinal_position
            """
            all_columns_result = session.execute(text(columns_query))
            all_columns = [row[0] for row in all_columns_result.fetchall()]
            
            # Definir ordem prioritária das colunas
            priority_columns = [
                'id', 'emissao', 'competencia', 'vencimento', 'date',
                'dfc_n1', 'dfc_n2', 'origem', 'category', 'subcategory', 'source',
                'description', 'value', 'company_id', 'created_at'
            ]
            
            # Criar lista ordenada
            ordered_columns = []
            for col in priority_columns:
                if col in all_columns:
                    ordered_columns.append(col)
            
            # Adicionar colunas restantes
            for col in all_columns:
                if col not in ordered_columns:
                    ordered_columns.append(col)
            
            # Buscar dados com colunas ordenadas
            columns_str = ', '.join(ordered_columns)
            query = f"SELECT {columns_str} FROM {table_name} LIMIT {limit}"
            result = session.execute(text(query))
            rows = result.fetchall()
            columns = ordered_columns
            
            # Obter estatísticas extras
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(emissao) as with_emissao,
                    COUNT(competencia) as with_competencia,
                    COUNT(vencimento) as with_vencimento,
                    COUNT(de_para_id) as with_de_para,
                    COUNT(empresa_id) as with_empresa,
                    COUNT(origem) as with_origem
                FROM financial_data
            """
            stats_result = session.execute(text(stats_query))
            stats = stats_result.fetchone()
            
            extra_stats = f"""
                <div style="background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>📊 Estatísticas das Colunas Principais</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                        <div>📅 <strong>Emissão:</strong> {stats[1]}/{stats[0]} registros</div>
                        <div>📅 <strong>Competência:</strong> {stats[2]}/{stats[0]} registros</div>
                        <div>📅 <strong>Vencimento:</strong> {stats[3]}/{stats[0]} registros</div>
                        <div>🔗 <strong>De/Para:</strong> {stats[4]}/{stats[0]} registros</div>
                        <div>🏢 <strong>Empresa:</strong> {stats[5]}/{stats[0]} registros</div>
                        <div>📍 <strong>Origem:</strong> {stats[6]}/{stats[0]} registros</div>
                    </div>
                </div>
            """
        else:
            # Para outras tabelas, usar busca normal
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = session.execute(text(query))
            columns = list(result.keys())  # Converter para lista
            rows = result.fetchall()
            extra_stats = ""
        
        session.close()
        
        # Gerar HTML da tabela
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tabela: {table_name}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 12px; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .header {{ background: #2c3e50; color: white; padding: 15px; border-radius: 5px; }}
                .btn {{ background: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; }}
                
                /* Destacar colunas importantes */
                .date-col {{ background-color: #e8f5e8 !important; }}
                .dfc-col {{ background-color: #fff3cd !important; }}
                .source-col {{ background-color: #d4edda !important; }}
                .value-col {{ background-color: #f8d7da !important; }}
                
                /* Colunas específicas */
                th:has-text("emissao"), th:has-text("competencia"), th:has-text("vencimento"), th:has-text("date") {{ background-color: #d4edda; }}
                th:has-text("dfc_n1"), th:has-text("dfc_n2") {{ background-color: #fff3cd; }}
                th:has-text("origem"), th:has-text("category"), th:has-text("subcategory"), th:has-text("source") {{ background-color: #d1ecf1; }}
                th:has-text("value") {{ background-color: #f5c6cb; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Tabela: {table_name}</h1>
                <p>Mostrando primeiros {limit} registros</p>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="/admin/database" class="btn">← Voltar</a>
                <a href="/admin/table/{table_name}?limit=500" class="btn">Ver 500 registros</a>
                <a href="/admin/table/{table_name}?limit=1000" class="btn">Ver 1000 registros</a>
            </div>
            
            {extra_stats}
            
            <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
        """
        
        # Adicionar cabeçalhos com classes específicas
        for col in columns:
            col_class = ""
            if col in ['emissao', 'competencia', 'vencimento', 'date']:
                col_class = ' style="background-color: #d4edda;"'
            elif col in ['dfc_n1', 'dfc_n2']:
                col_class = ' style="background-color: #fff3cd;"'
            elif col in ['origem', 'category', 'subcategory', 'source']:
                col_class = ' style="background-color: #d1ecf1;"'
            elif col == 'value':
                col_class = ' style="background-color: #f5c6cb;"'
                
            html_content += f"<th{col_class}>{col}</th>"
        
        html_content += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Adicionar dados
        for row in rows:
            html_content += "<tr>"
            for i, value in enumerate(row):
                # Truncar valores muito longos
                display_value = str(value)[:50] + "..." if value and len(str(value)) > 50 else str(value)
                
                # Aplicar classes nas células
                cell_class = ""
                if i < len(columns):
                    col_name = columns[i]
                    if col_name in ['emissao', 'competencia', 'vencimento', 'date']:
                        cell_class = ' style="background-color: #f0f9f0;"'
                    elif col_name in ['dfc_n1', 'dfc_n2']:
                        cell_class = ' style="background-color: #fffbe6;"'
                    elif col_name in ['origem', 'category', 'subcategory', 'source']:
                        cell_class = ' style="background-color: #e6f3ff;"'
                
                html_content += f"<td{cell_class}>{display_value}</td>"
            html_content += "</tr>"
        
        html_content += f"""
                </tbody>
            </table>
            </div>
            
            <div style="margin-top: 20px; text-align: center; color: #666;">
                <p>Total exibido: {len(rows)} registros</p>
                <p><strong>Legenda:</strong> 
                   <span style="background: #d4edda; padding: 2px 5px;">📅 Datas</span>
                   <span style="background: #fff3cd; padding: 2px 5px;">🏗️ DFC</span>
                   <span style="background: #d1ecf1; padding: 2px 5px;">📍 Origem/Categoria</span>
                   <span style="background: #f5c6cb; padding: 2px 5px;">💰 Valor</span>
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro</h1>
            <p>Erro ao buscar dados da tabela {table_name}:</p>
            <pre style="background: #f5f5f5; padding: 10px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar</a></p>
        </body>
        </html>
        """

@router.get("/table/{table_name}/structure", response_class=HTMLResponse)
async def view_table_structure(table_name: str):
    """Visualizar estrutura de uma tabela específica"""
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Obter informações das colunas
        structure_query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        result = session.execute(text(structure_query))
        columns = list(result.keys())
        rows = result.fetchall()
        
        session.close()
        
        # Gerar HTML para estrutura
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estrutura da Tabela {table_name} - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 10px 15px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin-right: 10px;
                }}
                .nav a:hover {{ background: #2980b9; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin-top: 20px;
                    background: white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left; 
                }}
                th {{ 
                    background-color: #34495e; 
                    color: white;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #e8f4f8; }}
                .nullable {{ color: #e74c3c; }}
                .not-nullable {{ color: #27ae60; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏗️ Estrutura da Tabela: {table_name}</h1>
                <p>Informações sobre colunas, tipos e restrições</p>
            </div>
            
            <div class="nav">
                <a href="/admin/database">← Voltar para Database</a>
                <a href="/admin/table/{table_name}">📊 Ver Dados</a>
            </div>
            
            <h2>📋 Colunas da Tabela</h2>
            <table>
                <thead>
                    <tr>
                        <th>Nome da Coluna</th>
                        <th>Tipo de Dados</th>
                        <th>Permite NULL</th>
                        <th>Valor Padrão</th>
                        <th>Tamanho Máximo</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            nullable_class = "nullable" if row_dict['is_nullable'] == 'YES' else "not-nullable"
            nullable_text = "SIM" if row_dict['is_nullable'] == 'YES' else "NÃO"
            
            html_content += f"""
                    <tr>
                        <td><strong>{row_dict['column_name']}</strong></td>
                        <td>{row_dict['data_type']}</td>
                        <td class="{nullable_class}">{nullable_text}</td>
                        <td>{row_dict['column_default'] or '-'}</td>
                        <td>{row_dict['character_maximum_length'] or '-'}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            
            <div style="margin-top: 30px; padding: 15px; background: #ecf0f1; border-radius: 5px;">
                <h3>📌 Legenda</h3>
                <p><span class="not-nullable">■</span> <strong>NÃO</strong> - Campo obrigatório (NOT NULL)</p>
                <p><span class="nullable">■</span> <strong>SIM</strong> - Campo opcional (permite NULL)</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro</h1>
            <p>Erro ao buscar estrutura da tabela {table_name}:</p>
            <pre style="background: #f5f5f5; padding: 10px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar</a></p>
        </body>
        </html>
        """

# ============================================================================
# NOVOS ENDPOINTS PARA TABELAS DE CADASTRO, PLANO DE CONTAS E DE/PARA
# ============================================================================

from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from database.connection_sqlalchemy import DatabaseSession
from database.schema_sqlalchemy import (
    GrupoEmpresa, Empresa, Categoria, PlanoDeContas, DePara
)

def generate_uuid() -> str:
    """Gera UUID único para identificação"""
    return str(uuid.uuid4())

def get_db():
    """Dependency para obter sessão do banco"""
    with DatabaseSession() as session:
        yield session

# ============================================================================
# ENDPOINTS DE CADASTRO
# ============================================================================



@router.post("/cadastro/grupos-empresa")
async def criar_grupo_empresa(
    nome: str,
    descricao: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cria novo grupo empresarial"""
    try:
        # Verificar se já existe
        existing = db.query(GrupoEmpresa).filter(GrupoEmpresa.nome == nome).first()
        if existing:
            raise HTTPException(status_code=400, detail="Grupo com este nome já existe")
        
        grupo = GrupoEmpresa(
            id=generate_uuid(),
            nome=nome,
            descricao=descricao,
            is_active=True
        )
        
        db.add(grupo)
        db.commit()
        
        return {"success": True, "id": grupo.id, "message": "Grupo criado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar grupo: {str(e)}")

@router.get("/cadastro/empresas", response_model=List[Dict[str, Any]])
async def listar_empresas(grupo_empresa_id: Optional[str] = Query(None, description="Filtrar empresas por grupo")):
    """Lista todas as empresas, opcionalmente filtradas por grupo empresarial"""
    try:
        engine = get_engine()
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        if grupo_empresa_id:
            # Filtrar por grupo específico
            cursor.execute("""
                SELECT id, nome 
                FROM empresas 
                WHERE is_active = true AND grupo_empresa_id = %s
                ORDER BY nome
            """, (grupo_empresa_id,))
        else:
            # Todas as empresas
            cursor.execute("""
                SELECT id, nome 
                FROM empresas 
                WHERE is_active = true 
                ORDER BY nome
            """)
        
        empresas = cursor.fetchall()
        
        # Fechar recursos
        cursor.close()
        connection.close()
        
        resultado = []
        
        if grupo_empresa_id:
            # Adicionar opção "Consolidado" para o grupo
            resultado.append({
                "id": f"{grupo_empresa_id}_consolidado",
                "nome": "Consolidado",
                "tipo": "consolidado",
                "grupo_empresa_id": grupo_empresa_id
            })
            
            # Adicionar empresas do grupo
            for empresa in empresas:
                resultado.append({
                    "id": str(empresa[0]),  # id
                    "nome": str(empresa[1]),  # nome
                    "tipo": "empresa"
                })
        else:
            # Todas as empresas (sem opção consolidada)
            for empresa in empresas:
                resultado.append({
                    "id": str(empresa[0]),  # id
                    "nome": str(empresa[1]),  # nome
                    "tipo": "empresa"
                })
        
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar empresas: {str(e)}")

@router.get("/cadastro/grupos-empresa", response_model=List[Dict[str, Any]])
async def listar_grupos_empresa():
    """Lista todos os grupos empresariais"""
    try:
        # Usar conexão direta para evitar conflitos do SQLAlchemy
        engine = get_engine()
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT id, nome 
            FROM grupos_empresa 
            WHERE is_active = true 
            ORDER BY nome
        """)
        grupos = cursor.fetchall()
        
        # Fechar recursos
        cursor.close()
        connection.close()
        
        return [
            {
                "id": str(grupo[0]),  # id
                "nome": str(grupo[1])  # nome
            }
            for grupo in grupos
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar grupos empresariais: {str(e)}")

@router.post("/cadastro/empresas")
async def criar_empresa(
    nome: str,
    grupo_empresa_id: str,
    cnpj: Optional[str] = None,
    razao_social: Optional[str] = None,
    nome_fantasia: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cria nova empresa"""
    try:
        # Verificar se grupo existe
        grupo = db.query(GrupoEmpresa).filter(GrupoEmpresa.id == grupo_empresa_id).first()
        if not grupo:
            raise HTTPException(status_code=400, detail="Grupo empresarial não encontrado")
        
        # Verificar se empresa já existe
        existing = db.query(Empresa).filter(Empresa.nome == nome).first()
        if existing:
            raise HTTPException(status_code=400, detail="Empresa com este nome já existe")
        
        empresa = Empresa(
            id=generate_uuid(),
            nome=nome,
            grupo_empresa_id=grupo_empresa_id,
            cnpj=cnpj,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia or nome,
            is_active=True
        )
        
        db.add(empresa)
        db.commit()
        
        return {"success": True, "id": empresa.id, "message": "Empresa criada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar empresa: {str(e)}")

@router.get("/cadastro/categorias", response_model=List[Dict[str, Any]])
async def listar_categorias(
    empresa_id: Optional[str] = Query(None, description="Filtrar por empresa"),
    db: Session = Depends(get_db)
):
    """Lista categorias, opcionalmente filtradas por empresa"""
    try:
        query = db.query(Categoria).filter(Categoria.is_active == True)
        
        if empresa_id:
            query = query.filter(Categoria.empresa_id == empresa_id)
        
        categorias = query.all()
        return [
            {
                "id": categoria.id,
                "nome": categoria.nome,
                "tipo": categoria.tipo,
                "empresa": categoria.empresa.nome if categoria.empresa else None,
                "descricao": categoria.descricao,
                "created_at": categoria.created_at.isoformat() if categoria.created_at else None
            }
            for categoria in categorias
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {str(e)}")

# ============================================================================
# ENDPOINTS DE PLANO DE CONTAS
# ============================================================================

@router.get("/plano-contas", response_model=List[Dict[str, Any]])
async def listar_plano_contas(
    empresa_id: Optional[str] = Query(None, description="Filtrar por empresa"),
    conta_pai: Optional[str] = Query(None, description="Filtrar por conta pai"),
    db: Session = Depends(get_db)
):
    """Lista plano de contas"""
    try:
        query = db.query(PlanoDeContas).filter(PlanoDeContas.is_active == True)
        
        if empresa_id:
            query = query.filter(PlanoDeContas.empresa_id == empresa_id)
        
        if conta_pai:
            query = query.filter(PlanoDeContas.conta_pai == conta_pai)
        
        plano_contas = query.order_by(PlanoDeContas.ordem).all()
        
        return [
            {
                "id": item.id,
                "conta": item.conta,
                "nome_conta": item.nome_conta,
                "conta_pai": item.conta_pai,
                "tipo_conta": item.tipo_conta,
                "nivel": item.nivel,
                "ordem": item.ordem,
                "classificacao_dre": item.classificacao_dre,
                "classificacao_dfc": item.classificacao_dfc,
                "centro_custo": item.centro_custo,
                "empresa": item.empresa.nome if item.empresa else None,
                "observacoes": item.observacoes
            }
            for item in plano_contas
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar plano de contas: {str(e)}")

@router.post("/plano-contas")
async def criar_plano_conta(
    empresa_id: str,
    conta: str,
    nome_conta: str,
    conta_pai: Optional[str] = None,
    tipo_conta: Optional[str] = None,
    nivel: int = 1,
    ordem: Optional[int] = None,
    classificacao_dre: Optional[str] = None,
    classificacao_dfc: Optional[str] = None,
    centro_custo: Optional[str] = None,
    observacoes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cria nova conta no plano de contas"""
    try:
        # Verificar se empresa existe
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=400, detail="Empresa não encontrada")
        
        # Verificar se conta já existe
        existing = db.query(PlanoDeContas).filter(
            PlanoDeContas.empresa_id == empresa_id,
            PlanoDeContas.conta == conta
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Conta já existe para esta empresa")
        
        # Definir ordem se não fornecida
        if ordem is None:
            max_ordem = db.query(PlanoDeContas).filter(
                PlanoDeContas.empresa_id == empresa_id
            ).order_by(PlanoDeContas.ordem.desc()).first()
            ordem = (max_ordem.ordem + 1) if max_ordem else 1
        
        plano_conta = PlanoDeContas(
            empresa_id=empresa_id,
            conta_pai=conta_pai,
            conta=conta,
            nome_conta=nome_conta,
            tipo_conta=tipo_conta,
            nivel=nivel,
            ordem=ordem,
            classificacao_dre=classificacao_dre,
            classificacao_dfc=classificacao_dfc,
            centro_custo=centro_custo,
            observacoes=observacoes,
            is_active=True
        )
        
        db.add(plano_conta)
        db.commit()
        
        return {"success": True, "id": plano_conta.id, "message": "Conta criada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar conta: {str(e)}")

# ============================================================================
# ENDPOINTS DE DE/PARA
# ============================================================================

@router.get("/de-para", response_model=List[Dict[str, Any]])
async def listar_de_para(
    empresa_id: Optional[str] = Query(None, description="Filtrar por empresa"),
    tipo_mapeamento: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: Session = Depends(get_db)
):
    """Lista tabela de mapeamento de_para"""
    try:
        query = db.query(DePara).filter(DePara.is_active == True)
        
        if empresa_id:
            query = query.filter(DePara.empresa_id == empresa_id)
        
        if tipo_mapeamento:
            query = query.filter(DePara.tipo_mapeamento == tipo_mapeamento)
        
        de_para_list = query.all()
        
        return [
            {
                "id": item.id,
                "origem_sistema": item.origem_sistema,
                "codigo_origem": item.codigo_origem,
                "descricao_origem": item.descricao_origem,
                "codigo_destino": item.codigo_destino,
                "descricao_destino": item.descricao_destino,
                "tipo_mapeamento": item.tipo_mapeamento,
                "empresa": item.empresa.nome if item.empresa else None,
                "observacoes": item.observacoes
            }
            for item in de_para_list
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar de_para: {str(e)}")

@router.post("/de-para")
async def criar_de_para(
    empresa_id: str,
    codigo_origem: str,
    descricao_origem: str,
    codigo_destino: str,
    descricao_destino: str,
    origem_sistema: Optional[str] = None,
    tipo_mapeamento: Optional[str] = None,
    observacoes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cria novo mapeamento de_para"""
    try:
        # Verificar se empresa existe
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=400, detail="Empresa não encontrada")
        
        # Verificar se mapeamento já existe
        existing = db.query(DePara).filter(
            DePara.empresa_id == empresa_id,
            DePara.codigo_origem == codigo_origem,
            DePara.origem_sistema == origem_sistema
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Mapeamento já existe para esta origem")
        
        de_para = DePara(
            empresa_id=empresa_id,
            origem_sistema=origem_sistema,
            codigo_origem=codigo_origem,
            descricao_origem=descricao_origem,
            codigo_destino=codigo_destino,
            descricao_destino=descricao_destino,
            tipo_mapeamento=tipo_mapeamento,
            observacoes=observacoes,
            is_active=True
        )
        
        db.add(de_para)
        db.commit()
        
        return {"success": True, "id": de_para.id, "message": "Mapeamento criado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar mapeamento: {str(e)}")

# ============================================================================
# ENDPOINTS DE ESTATÍSTICAS
# ============================================================================

@router.get("/stats/overview")
async def estatisticas_gerais(db: Session = Depends(get_db)):
    """Estatísticas gerais do sistema"""
    try:
        stats = {
            "grupos_empresa": db.query(GrupoEmpresa).filter(GrupoEmpresa.is_active == True).count(),
            "empresas": db.query(Empresa).filter(Empresa.is_active == True).count(),
            "categorias": db.query(Categoria).filter(Categoria.is_active == True).count(),
            "plano_contas": db.query(PlanoDeContas).filter(PlanoDeContas.is_active == True).count(),
            "de_para": db.query(DePara).filter(DePara.is_active == True).count()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.get("/stats/empresa/{empresa_id}")
async def estatisticas_empresa(empresa_id: str, db: Session = Depends(get_db)):
    """Estatísticas específicas de uma empresa"""
    try:
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        stats = {
            "empresa": {
                "id": empresa.id,
                "nome": empresa.nome,
                "grupo": empresa.grupo_empresa.nome if empresa.grupo_empresa else None
            },
            "categorias": db.query(Categoria).filter(
                Categoria.empresa_id == empresa_id,
                Categoria.is_active == True
            ).count(),
            "plano_contas": db.query(PlanoDeContas).filter(
                PlanoDeContas.empresa_id == empresa_id,
                PlanoDeContas.is_active == True
            ).count(),
            "de_para": db.query(DePara).filter(
                DePara.empresa_id == empresa_id,
                DePara.is_active == True
            ).count()
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas da empresa: {str(e)}")

# ============================================================================
# ENDPOINTS DE BACKUP
# ============================================================================

@router.get("/backups", response_class=HTMLResponse)
async def view_backups():
    """Interface para gerenciar backups"""
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Buscar todas as tabelas de backup
        backup_query = """
        SELECT 
            table_name,
            table_type,
            CASE 
                WHEN table_name LIKE '%_backup_%' THEN 'BACKUP'
                ELSE 'ORIGINAL'
            END as object_type,
            CASE 
                WHEN table_name LIKE '%_backup_%' THEN 
                    SUBSTRING(table_name FROM 'backup_([0-9]{8})$')
                ELSE NULL
            END as backup_date
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND (
            table_name LIKE '%_backup_%' 
            OR table_name LIKE 'backup_summary_%'
        )
        ORDER BY 
            CASE 
                WHEN table_name LIKE '%_backup_%' THEN 1
                WHEN table_name LIKE 'backup_summary_%' THEN 2
                ELSE 3
            END,
            table_name
        """
        
        backup_result = session.execute(text(backup_query)).fetchall()
        
        # Organizar backups por data
        backup_groups = {}
        for row in backup_result:
            backup_date = row.backup_date or 'summary'
            if backup_date not in backup_groups:
                backup_groups[backup_date] = []
            backup_groups[backup_date].append({
                'table_name': row.table_name,
                'table_type': row.table_type,
                'object_type': row.object_type,
                'backup_date': row.backup_date
            })
        
        # Contar registros de cada backup
        for date, backups in backup_groups.items():
            for backup in backups:
                try:
                    count_query = f"SELECT COUNT(*) FROM {backup['table_name']}"
                    count = session.execute(text(count_query)).scalar()
                    backup['record_count'] = count
                except Exception as e:
                    backup['record_count'] = f"Erro: {e}"
        
        session.close()
        
        # Gerar HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gerenciar Backups - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: #16a085; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }}
                .backup-section {{
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background: #f9f9f9;
                }}
                .backup-date {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #16a085;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #16a085;
                    padding-bottom: 10px;
                }}
                .backup-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 15px;
                }}
                .backup-card {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    background: white;
                    transition: transform 0.2s;
                }}
                .backup-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
                .backup-name {{
                    font-weight: bold;
                    color: #2c3e50;
                    font-size: 16px;
                    margin-bottom: 10px;
                }}
                .backup-count {{
                    color: #27ae60;
                    font-size: 20px;
                    font-weight: bold;
                }}
                .backup-type {{
                    color: #7f8c8d;
                    font-size: 14px;
                    margin-top: 5px;
                }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 8px 15px; 
                    text-decoration: none; 
                    border-radius: 3px; 
                    margin: 5px;
                    display: inline-block;
                }}
                .btn:hover {{ background: #2980b9; }}
                .btn-danger {{ 
                    background: #e74c3c; 
                }}
                .btn-danger:hover {{ 
                    background: #c0392b; 
                }}
                .btn-success {{ 
                    background: #27ae60; 
                }}
                .btn-success:hover {{ 
                    background: #229954; 
                }}
                .actions {{
                    margin-top: 15px;
                    text-align: center;
                }}
                .no-backups {{
                    text-align: center;
                    color: #7f8c8d;
                    font-style: italic;
                    padding: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💾 Sistema de Backups - TAG Financeiro</h1>
                    <p>Gerenciamento de backups automáticos das tabelas e views</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <a href="/admin/database" class="btn">← Voltar ao Admin</a>
                    <a href="/admin/create-backup" class="btn btn-success">🔄 Criar Novo Backup</a>
                </div>
        """
        
        if not backup_groups:
            html_content += """
                <div class="no-backups">
                    <h2>📦 Nenhum backup encontrado</h2>
                    <p>Clique em "Criar Novo Backup" para fazer o primeiro backup do sistema.</p>
                </div>
            """
        else:
            for date, backups in backup_groups.items():
                if date == 'summary':
                    section_title = "📋 Tabelas de Resumo"
                    date_display = "Resumo dos Backups"
                else:
                    try:
                        date_obj = pd.Timestamp.strptime(date, "%Y%m%d")
                        date_display = date_obj.strftime("%d/%m/%Y")
                    except:
                        date_display = date
                    section_title = f"📅 Backup de {date_display}"
                
                html_content += f"""
                    <div class="backup-section">
                        <div class="backup-date">{section_title}</div>
                        <div class="backup-grid">
                """
                
                for backup in backups:
                    if backup['object_type'] == 'BACKUP':
                        icon = "📦"
                        color = "#16a085"
                    else:
                        icon = "📋"
                        color = "#7f8c8d"
                    
                    # Construir o botão de remoção separadamente
                    delete_button = ""
                    if date != 'summary':
                        delete_button = f'<a href="/admin/delete-backup/{date}" class="btn btn-danger" onclick="return confirm(\\"Tem certeza que deseja remover este backup?\\")">🗑️ Remover</a>'
                    
                    html_content += f"""
                        <div class="backup-card">
                            <div class="backup-name" style="color: {color};">{icon} {backup['table_name']}</div>
                            <div class="backup-count">{backup['record_count']} registros</div>
                            <div class="backup-type">Tipo: {backup['table_type']}</div>
                            <div class="actions">
                                <a href="/admin/table/{backup['table_name']}" class="btn">Ver Dados</a>
                                <a href="/admin/table/{backup['table_name']}/structure" class="btn">Estrutura</a>
                                {delete_button}
                            </div>
                        </div>
                    """
                
                html_content += """
                        </div>
                    </div>
                """
        
        html_content += """
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>💡 Dica: Os backups são criados automaticamente com data no nome (formato: YYYYMMDD)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro ao Carregar Backups</h1>
            <p>Não foi possível carregar os backups:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/database">← Voltar ao Admin</a></p>
        </body>
        </html>
        """

@router.get("/create-backup", response_class=HTMLResponse)
async def create_backup_interface():
    """Interface para criar novo backup"""
    try:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Criar Backup - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: #e67e22; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }}
                .info-box {{
                    background: #ecf0f1;
                    border-left: 4px solid #e67e22;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 12px 20px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 10px;
                    display: inline-block;
                    font-size: 16px;
                }}
                .btn:hover {{ background: #2980b9; }}
                .btn-success {{ 
                    background: #27ae60; 
                }}
                .btn-success:hover {{ 
                    background: #229954; 
                }}
                .btn-warning {{ 
                    background: #f39c12; 
                }}
                .btn-warning:hover {{ 
                    background: #e67e22; 
                }}
                .backup-list {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .backup-item {{
                    padding: 10px;
                    border-bottom: 1px solid #dee2e6;
                }}
                .backup-item:last-child {{
                    border-bottom: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔄 Criar Novo Backup - TAG Financeiro</h1>
                    <p>Criação de backup completo das tabelas e views do sistema</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <a href="/admin/backups" class="btn">← Voltar aos Backups</a>
                    <a href="/admin/database" class="btn">🏠 Admin Principal</a>
                </div>
                
                <div class="info-box">
                    <h3>📋 O que será backupado:</h3>
                    <div class="backup-list">
                        <div class="backup-item"><strong>📊 Tabelas de Estrutura:</strong> dre_structure_n0, dre_structure_n1, dre_structure_n2, dfc_structure_n1, dfc_structure_n2</div>
                        <div class="backup-item"><strong>👁️ Views DRE:</strong> v_dre_n0_completo, v_dre_n0_simples, v_dre_n0_por_periodo</div>
                        <div class="backup-item"><strong>💾 Tabelas Principais:</strong> financial_data, de_para, plano_de_contas, grupo_empresa</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <h3>🚀 Executar Backup</h3>
                    <p>Clique no botão abaixo para executar o script de backup:</p>
                    <a href="/admin/execute-backup" class="btn btn-success" style="font-size: 18px; padding: 15px 30px;">🔄 Executar Backup Agora</a>
                </div>
                
                <div class="info-box">
                    <h3>💡 Informações:</h3>
                    <ul>
                        <li>O backup será criado com a data atual no nome (formato: YYYYMMDD)</li>
                        <li>Uma tabela de resumo será criada para facilitar o gerenciamento</li>
                        <li>O processo pode levar alguns minutos dependendo do volume de dados</li>
                        <li>Após a conclusão, você será redirecionado para a lista de backups</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro ao Carregar Interface</h1>
            <p>Não foi possível carregar a interface de criação de backup:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/backups">← Voltar aos Backups</a></p>
        </body>
        </html>
        """

@router.get("/execute-backup", response_class=HTMLResponse)
async def execute_backup():
    """Executa o script de backup e mostra o resultado"""
    try:
        import subprocess
        import sys
        import os
        
        # Caminho para o script de backup na pasta scripts
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(backend_dir, "scripts", "create_backup_with_date.py")
        
        # Verificar se o script existe
        if not os.path.exists(script_path):
            raise HTTPException(status_code=500, detail=f"Script de backup não encontrado em: {script_path}")
        
        # Executar o script a partir do diretório backend
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=backend_dir)
        
        if result.returncode == 0:
            # Backup bem-sucedido
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Backup Concluído - TAG Financeiro</title>
                <meta charset="utf-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        background-color: #f5f5f5;
                    }}
                    .container {{ 
                        max-width: 800px; 
                        margin: 0 auto; 
                        background: white; 
                        padding: 20px; 
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{ 
                        background: #27ae60; 
                        color: white; 
                        padding: 20px; 
                        border-radius: 5px; 
                        margin-bottom: 20px;
                    }}
                    .success-box {{
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        color: #155724;
                        padding: 20px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .btn {{ 
                        background: #3498db; 
                        color: white; 
                        padding: 12px 20px; 
                        text-decoration: none; 
                        border-radius: 5px; 
                        margin: 10px;
                        display: inline-block;
                    }}
                    .btn:hover {{ background: #2980b9; }}
                    .btn-success {{ 
                        background: #27ae60; 
                    }}
                    .btn-success:hover {{ 
                        background: #229954; 
                    }}
                    pre {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                        white-space: pre-wrap;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Backup Concluído com Sucesso!</h1>
                        <p>O backup foi criado e está disponível para gerenciamento</p>
                    </div>
                    
                    <div class="success-box">
                        <h3>🎉 Backup Executado com Sucesso!</h3>
                        <p>O script de backup foi executado e todas as tabelas foram backupadas.</p>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <h3>📋 Log de Execução:</h3>
                        <pre>{result.stdout}</pre>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="/admin/backups" class="btn btn-success">📦 Ver Backups</a>
                        <a href="/admin/database" class="btn">🏠 Admin Principal</a>
                    </div>
                    
                    <div style="margin-top: 30px; text-align: center; color: #666;">
                        <p>💡 O backup foi criado com sucesso! Você pode agora gerenciar os backups através da interface.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            # Erro no backup
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial; padding: 20px;">
                <h1>❌ Erro no Backup</h1>
                <p>Ocorreu um erro durante a execução do backup:</p>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{result.stderr}</pre>
                <p><a href="/admin/create-backup">← Tentar Novamente</a></p>
            </body>
            </html>
            """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro ao Executar Backup</h1>
            <p>Não foi possível executar o script de backup:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/create-backup">← Voltar</a></p>
        </body>
        </html>
        """

@router.get("/delete-backup/{backup_date}", response_class=HTMLResponse)
async def delete_backup_interface(backup_date: str):
    """Interface para confirmar e deletar backup"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Remover Backup - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: #e74c3c; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }}
                .warning-box {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 12px 20px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 10px;
                    display: inline-block;
                }}
                .btn:hover {{ background: #2980b9; }}
                .btn-danger {{ 
                    background: #e74c3c; 
                }}
                .btn-danger:hover {{ 
                    background: #c0392b; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🗑️ Remover Backup - TAG Financeiro</h1>
                    <p>Confirmação para remoção de backup</p>
                </div>
                
                <div class="warning-box">
                    <h3>⚠️ Atenção!</h3>
                    <p>Você está prestes a remover o backup da data <strong>{backup_date}</strong>.</p>
                    <p>Esta ação irá:</p>
                    <ul>
                        <li>Remover todas as tabelas de backup desta data</li>
                        <li>Remover a tabela de resumo</li>
                        <li>Esta ação <strong>NÃO PODE</strong> ser desfeita</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <h3>🤔 Confirmar Remoção?</h3>
                    <p>Deseja realmente remover este backup?</p>
                    <a href="/admin/confirm-delete-backup/{backup_date}" class="btn btn-danger">🗑️ Sim, Remover Backup</a>
                    <a href="/admin/backups" class="btn">❌ Cancelar</a>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>💡 Se você não tem certeza, é recomendado manter o backup por segurança.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro ao Carregar Interface</h1>
            <p>Não foi possível carregar a interface de remoção:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/backups">← Voltar aos Backups</a></p>
        </body>
        </html>
        """

@router.get("/confirm-delete-backup/{backup_date}", response_class=HTMLResponse)
async def confirm_delete_backup(backup_date: str):
    """Confirma e executa a remoção do backup"""
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Verificar se a tabela de resumo existe
        summary_table = f"backup_summary_{backup_date}"
        check_query = f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = '{summary_table}'
        """
        
        result = session.execute(text(check_query))
        if not result.fetchone():
            return """
            <html>
            <body style="font-family: Arial; padding: 20px;">
                <h1>❌ Backup Não Encontrado</h1>
                <p>O backup especificado não foi encontrado.</p>
                <p><a href="/admin/backups">← Voltar aos Backups</a></p>
            </body>
            </html>
            """
        
        # Buscar todas as tabelas de backup desta data
        backup_tables_query = f"""
        SELECT backup_name 
        FROM {summary_table}
        WHERE backup_name IS NOT NULL
        """
        
        result = session.execute(text(backup_tables_query))
        backup_tables = [row.backup_name for row in result]
        
        # Remover tabelas de backup
        deleted_tables = []
        for table_name in backup_tables:
            try:
                drop_query = f"DROP TABLE IF EXISTS {table_name}"
                session.execute(text(drop_query))
                deleted_tables.append(table_name)
            except Exception as e:
                print(f"Erro ao remover tabela {table_name}: {e}")
        
        # Remover tabela de resumo
        try:
            drop_summary_query = f"DROP TABLE IF EXISTS {summary_table}"
            session.execute(text(drop_summary_query))
        except Exception as e:
            print(f"Erro ao remover tabela de resumo: {e}")
        
        session.commit()
        session.close()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backup Removido - TAG Financeiro</title>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    background: #27ae60; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px;
                }}
                .success-box {{
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .btn {{ 
                    background: #3498db; 
                    color: white; 
                    padding: 12px 20px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 10px;
                    display: inline-block;
                }}
                .btn:hover {{ background: #2980b9; }}
                .btn-success {{ 
                    background: #27ae60; 
                }}
                .btn-success:hover {{ 
                    background: #229954; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Backup Removido com Sucesso!</h1>
                    <p>O backup da data {backup_date} foi removido do sistema</p>
                </div>
                
                <div class="success-box">
                    <h3>🗑️ Remoção Concluída</h3>
                    <p>O backup foi removido com sucesso.</p>
                    <p><strong>Tabelas removidas:</strong> {len(deleted_tables)}</p>
                    <p><strong>Data do backup:</strong> {backup_date}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/admin/backups" class="btn btn-success">📦 Voltar aos Backups</a>
                    <a href="/admin/database" class="btn">🏠 Admin Principal</a>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>💡 O backup foi removido permanentemente do sistema.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>❌ Erro ao Remover Backup</h1>
            <p>Ocorreu um erro durante a remoção do backup:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            <p><a href="/admin/backups">← Voltar aos Backups</a></p>
        </body>
        </html>
        """
