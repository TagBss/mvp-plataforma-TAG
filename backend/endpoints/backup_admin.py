from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.connection_sqlalchemy import get_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any
import os
from datetime import datetime

router = APIRouter(prefix="/admin/backups", tags=["admin-backups"])

def get_db():
    """Dependency para obter sessão do banco"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
async def list_backups(db: Session = Depends(get_db)):
    """
    Lista todos os backups disponíveis no sistema
    """
    try:
        # Buscar todas as tabelas de backup
        query = text("""
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
        """)
        
        result = db.execute(query)
        backups = []
        
        for row in result:
            backup_info = {
                "table_name": row.table_name,
                "table_type": row.table_type,
                "object_type": row.object_type,
                "backup_date": row.backup_date,
                "formatted_date": None,
                "record_count": 0
            }
            
            # Formatar data se disponível
            if row.backup_date:
                try:
                    date_obj = datetime.strptime(row.backup_date, "%Y%m%d")
                    backup_info["formatted_date"] = date_obj.strftime("%d/%m/%Y")
                except:
                    backup_info["formatted_date"] = row.backup_date
            
            # Contar registros
            try:
                count_query = text(f"SELECT COUNT(*) as count FROM {row.table_name}")
                count_result = db.execute(count_query)
                backup_info["record_count"] = count_result.fetchone().count
            except:
                backup_info["record_count"] = 0
            
            backups.append(backup_info)
        
        return {
            "success": True,
            "backups": backups,
            "total_backups": len(backups)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar backups: {str(e)}")

@router.get("/summary/{backup_date}")
async def get_backup_summary(backup_date: str, db: Session = Depends(get_db)):
    """
    Obtém detalhes de um backup específico pela data
    """
    try:
        summary_table = f"backup_summary_{backup_date}"
        
        # Verificar se a tabela de resumo existe
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = :table_name
        """)
        
        result = db.execute(check_query, {"table_name": summary_table})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Backup da data {backup_date} não encontrado")
        
        # Buscar detalhes do backup
        summary_query = text(f"""
            SELECT 
                original_name,
                backup_name,
                table_type,
                record_count,
                backup_date,
                backup_time
            FROM {summary_table}
            ORDER BY backup_time
        """)
        
        result = db.execute(summary_query)
        backup_details = []
        
        for row in result:
            backup_details.append({
                "original_name": row.original_name,
                "backup_name": row.backup_name,
                "table_type": row.table_type,
                "record_count": row.record_count,
                "backup_date": row.backup_date.isoformat() if row.backup_date else None,
                "backup_time": row.backup_time.isoformat() if row.backup_time else None
            })
        
        return {
            "success": True,
            "backup_date": backup_date,
            "formatted_date": datetime.strptime(backup_date, "%Y%m%d").strftime("%d/%m/%Y"),
            "details": backup_details,
            "total_objects": len(backup_details)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo do backup: {str(e)}")

@router.get("/compare/{backup_date}")
async def compare_backup_with_original(backup_date: str, db: Session = Depends(get_db)):
    """
    Compara um backup com as tabelas originais
    """
    try:
        summary_table = f"backup_summary_{backup_date}"
        
        # Verificar se a tabela de resumo existe
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = :table_name
        """)
        
        result = db.execute(check_query, {"table_name": summary_table})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Backup da data {backup_date} não encontrado")
        
        # Buscar detalhes do backup
        summary_query = text(f"""
            SELECT 
                original_name,
                backup_name,
                record_count
            FROM {summary_table}
            ORDER BY original_name
        """)
        
        result = db.execute(summary_query)
        comparison = []
        
        for row in result:
            original_name = row.original_name
            backup_name = row.backup_name
            backup_count = row.record_count
            
            # Contar registros na tabela original
            try:
                original_count_query = text(f"SELECT COUNT(*) as count FROM {original_name}")
                original_result = db.execute(original_count_query)
                original_count = original_result.fetchone().count
            except:
                original_count = 0
            
            # Verificar se há diferença
            has_difference = backup_count != original_count
            
            comparison.append({
                "original_name": original_name,
                "backup_name": backup_name,
                "original_count": original_count,
                "backup_count": backup_count,
                "difference": original_count - backup_count,
                "has_difference": has_difference,
                "status": "✅ Sincronizado" if not has_difference else "⚠️ Diferença detectada"
            })
        
        return {
            "success": True,
            "backup_date": backup_date,
            "formatted_date": datetime.strptime(backup_date, "%Y%m%d").strftime("%d/%m/%Y"),
            "comparison": comparison,
            "total_objects": len(comparison),
            "synchronized": sum(1 for c in comparison if not c["has_difference"]),
            "with_differences": sum(1 for c in comparison if c["has_difference"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao comparar backup: {str(e)}")

@router.delete("/{backup_date}")
async def delete_backup(backup_date: str, db: Session = Depends(get_db)):
    """
    Remove um backup específico e sua tabela de resumo
    """
    try:
        summary_table = f"backup_summary_{backup_date}"
        
        # Verificar se a tabela de resumo existe
        check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = :table_name
        """)
        
        result = db.execute(check_query, {"table_name": summary_table})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Backup da data {backup_date} não encontrado")
        
        # Buscar todas as tabelas de backup desta data
        backup_tables_query = text(f"""
            SELECT backup_name 
            FROM {summary_table}
            WHERE backup_name IS NOT NULL
        """)
        
        result = db.execute(backup_tables_query)
        backup_tables = [row.backup_name for row in result]
        
        # Remover tabelas de backup
        deleted_tables = []
        for table_name in backup_tables:
            try:
                drop_query = text(f"DROP TABLE IF EXISTS {table_name}")
                db.execute(drop_query)
                deleted_tables.append(table_name)
            except Exception as e:
                print(f"Erro ao remover tabela {table_name}: {e}")
        
        # Remover tabela de resumo
        try:
            drop_summary_query = text(f"DROP TABLE IF EXISTS {summary_table}")
            db.execute(drop_summary_query)
        except Exception as e:
            print(f"Erro ao remover tabela de resumo: {e}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Backup da data {backup_date} removido com sucesso",
            "deleted_tables": deleted_tables,
            "total_deleted": len(deleted_tables)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao remover backup: {str(e)}")

@router.get("/stats")
async def get_backup_statistics(db: Session = Depends(get_db)):
    """
    Obtém estatísticas gerais dos backups
    """
    try:
        # Contar backups por data
        stats_query = text("""
            SELECT 
                SUBSTRING(table_name FROM 'backup_([0-9]{8})$') as backup_date,
                COUNT(*) as table_count,
                SUM(
                    CASE 
                        WHEN table_name LIKE '%_backup_%' THEN 1
                        ELSE 0
                    END
                ) as backup_tables,
                SUM(
                    CASE 
                        WHEN table_name LIKE 'backup_summary_%' THEN 1
                        ELSE 0
                    END
                ) as summary_tables
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name LIKE '%_backup_%'
            GROUP BY SUBSTRING(table_name FROM 'backup_([0-9]{8})$')
            ORDER BY backup_date DESC
        """)
        
        result = db.execute(stats_query)
        backup_stats = []
        
        for row in result:
            if row.backup_date:
                try:
                    date_obj = datetime.strptime(row.backup_date, "%Y%m%d")
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                except:
                    formatted_date = row.backup_date
                
                backup_stats.append({
                    "backup_date": row.backup_date,
                    "formatted_date": formatted_date,
                    "table_count": row.table_count,
                    "backup_tables": row.backup_tables,
                    "summary_tables": row.summary_tables
                })
        
        # Estatísticas gerais
        total_backups = len(backup_stats)
        total_tables = sum(stat["table_count"] for stat in backup_stats)
        
        return {
            "success": True,
            "total_backups": total_backups,
            "total_tables": total_tables,
            "backup_dates": backup_stats,
            "latest_backup": backup_stats[0] if backup_stats else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
