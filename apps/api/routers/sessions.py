import os
import json
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.session_store import (
    get_db, create_session, get_session, update_session_status, delete_session, DBTransaction, DBSessionRule, clean_expired_sessions
)
from services.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

# Define UPLOAD_DIR
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE_MB = 10

class SessionResponseSchema(BaseModel):
    sessionId: str
    createdAt: str
    expiresAt: str
    status: str

class StatusResponseSchema(BaseModel):
    sessionId: str
    status: str
    errorMessage: Optional[str]
    updatedAt: Optional[str]

class ColumnMappingSchema(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    debit: Optional[str] = None
    credit: Optional[str] = None
    amount: Optional[str] = None
    balance: Optional[str] = None

@router.post("", response_model=SessionResponseSchema)
def api_create_session(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new ephemeral session."""
    try:
        # Trigger lazy clean up of expired sessions in the background
        background_tasks.add_task(clean_expired_sessions, db)
        
        session = create_session(db)
        return {
            "sessionId": session.id,
            "createdAt": session.created_at.isoformat(),
            "expiresAt": session.expires_at.isoformat(),
            "status": session.status.status if session.status else "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/{session_id}/status", response_model=StatusResponseSchema)
def api_get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Retrieve the processing status of a session."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    status_info = session.status
    return {
        "sessionId": session.id,
        "status": status_info.status if status_info else "unknown",
        "errorMessage": status_info.error_message if status_info else None,
        "updatedAt": status_info.updated_at.isoformat() if status_info else None
    }

@router.delete("/{session_id}")
def api_delete_session(session_id: str, db: Session = Depends(get_db)):
    """Explicitly delete a session and all its associated database entries and upload files."""
    # 1. Fetch session to ensure it exists
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 2. Delete upload directory if it exists
    session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
    if os.path.exists(session_upload_dir):
        try:
            shutil.rmtree(session_upload_dir)
        except Exception as e:
            print(f"Warning: Failed to delete directory {session_upload_dir}: {str(e)}")
            
    # 3. Delete DB session and transactions (cascade deletes transactions)
    delete_session(db, session_id)
    return {"status": "deleted", "sessionId": session_id}

@router.post("/{session_id}/upload")
async def api_upload_statement(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a bank statement (CSV or Excel format) to the session."""
    # 1. Verify session exists
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 2. Check file format (extension)
    filename = file.filename or ""
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext not in ['.csv', '.xlsx']:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Only CSV and Excel (.xlsx) statements are supported."
        )
        
    # 3. Create session upload directory
    session_upload_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    file_path = os.path.join(session_upload_dir, f"statement{file_ext}")
    
    # 4. Save file while validating size (chunked read)
    total_bytes = 0
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    
    try:
        # If standard cleanup did not run, check if files of other type exist and remove them
        other_ext = '.csv' if file_ext == '.xlsx' else '.xlsx'
        other_path = os.path.join(session_upload_dir, f"statement{other_ext}")
        if os.path.exists(other_path):
            os.remove(other_path)
            
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    # Clean up partial file
                    buffer.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=413, 
                        detail=f"Uploaded file exceeds the maximum size limit of {MAX_FILE_SIZE_MB} MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
    # GAP-08: Sanitize filename for safe logging/response (SEC-01)
    safe_filename = os.path.basename(filename)

    # BUG-08: Reject empty files immediately (ING-01)
    if total_bytes == 0:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="File is empty. Please upload a valid bank statement.")

    # BUG-07: Reject files whose content is a PDF regardless of extension (ING-04)
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(5)
        if magic.startswith(b'%PDF'):
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail="The uploaded file appears to be a PDF. Only CSV and Excel (.xlsx) statements are supported."
            )
    except HTTPException:
        raise
    except Exception:
        pass  # If magic check fails, let parser handle it

    return {
        "sessionId": session_id,
        "filename": safe_filename,
        "sizeBytes": total_bytes,
        "message": "File uploaded successfully. Ready to run analysis."
    }

@router.post("/{session_id}/analyze")
def api_analyze_session(
    session_id: str,
    payload: Optional[ColumnMappingSchema] = None,
    db: Session = Depends(get_db)
):
    """Run the ingestion and cleaning pipeline for the uploaded file."""
    # 1. Verify session exists
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 2. Check if statement file is present (.csv or .xlsx)
    file_path_csv = os.path.join(UPLOAD_DIR, session_id, "statement.csv")
    file_path_xlsx = os.path.join(UPLOAD_DIR, session_id, "statement.xlsx")
    
    if os.path.exists(file_path_csv):
        file_path = file_path_csv
    elif os.path.exists(file_path_xlsx):
        file_path = file_path_xlsx
    else:
        raise HTTPException(
            status_code=400, 
            detail="No uploaded statement file found. Please upload a CSV or Excel statement first."
        )
        
    try:
        from services.pipeline.orchestrator import run_pipeline, ColumnMappingRequiredError
        
        # Strip out any keys in manual mapping that are null or empty
        manual_mapping_dict = None
        if payload:
            manual_mapping_dict = {k: v for k, v in payload.dict().items() if v}
            if not manual_mapping_dict:
                manual_mapping_dict = None
                
        # Run pipeline synchronously for the prototype
        meta_summary = run_pipeline(db, session_id, file_path, manual_mapping=manual_mapping_dict)
        return {
            "status": "success",
            "sessionId": session_id,
            "summary": meta_summary
        }
    except ColumnMappingRequiredError as cm_err:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MAPPING_REQUIRED",
                "message": "Could not auto-detect essential columns. Please map them manually.",
                "headers": cm_err.headers,
                "suggested_mapping": cm_err.suggested_mapping
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pipeline processing failed: {str(e)}")

@router.get("/{session_id}/transactions")
def api_get_transactions(
    session_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    category: Optional[str] = None,
    search: Optional[str] = None,
    fromDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    toDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Retrieve paginated list of transactions for this session, with optional search, category and date filters."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = db.query(DBTransaction).filter(DBTransaction.session_id == session_id)
    
    # Apply category filter
    if category:
        query = query.filter(DBTransaction.category == category)
        
    # Apply search filter (checks merchant name and description)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            DBTransaction.merchant.like(search_term) |
            DBTransaction.clean_description.like(search_term) |
            DBTransaction.raw_description.like(search_term)
        )
        
    # Apply date filters
    if fromDate:
        query = query.filter(DBTransaction.date >= fromDate)
    if toDate:
        query = query.filter(DBTransaction.date <= toDate)
        
    # Get total match count
    total_count = query.count()
    
    # Sort transactions chronologically (ascending date)
    query = query.order_by(DBTransaction.date.asc(), DBTransaction.id.asc())
    
    # Apply pagination offset
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Transform results to schema list
    transactions_list = []
    for tx in results:
        transactions_list.append({
            "id": tx.id,
            "sessionId": tx.session_id,
            "date": tx.date,
            "rawDescription": tx.raw_description,
            "cleanDescription": tx.clean_description,
            "merchant": tx.merchant,
            "amount": tx.amount,
            "type": tx.type,
            "category": tx.category,
            "categoryConfidence": tx.category_confidence,
            "categorySource": tx.category_source,
            "isRecurring": tx.is_recurring,
            "recurringGroupId": tx.recurring_group_id
        })
        
    pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    
    return {
        "transactions": transactions_list,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": pages
    }

@router.get("/{session_id}/categories")
def api_get_categories_aggregates(session_id: str, db: Session = Depends(get_db)):
    """Retrieve aggregated spend per category (total spent and percentage)."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # We only sum absolute debits (expenses) for category spend aggregates.
    transactions = db.query(DBTransaction).filter(
        DBTransaction.session_id == session_id,
        DBTransaction.type == "debit"
    ).all()
    
    # Group by category, filtering out internal transfers
    categories_sum = {}
    for tx in transactions:
        is_internal = False
        if tx.metadata_json:
            try:
                meta = json.loads(tx.metadata_json)
                is_internal = bool(meta.get("is_internal_transfer", False))
            except Exception:
                pass
        if is_internal:
            continue
            
        cat = tx.category
        categories_sum[cat] = categories_sum.get(cat, 0.0) + abs(tx.amount)
        
    total_spend = sum(categories_sum.values())
    
    aggregates = []
    for cat, amt in categories_sum.items():
        percentage = (amt / total_spend * 100.0) if total_spend > 0 else 0.0
        aggregates.append({
            "category": cat,
            "amount": round(amt, 2),
            "percentage": round(percentage, 2)
        })
        
    # Sort aggregates by amount descending
    aggregates.sort(key=lambda x: x["amount"], reverse=True)
    
    return aggregates

class OverrideCategorySchema(BaseModel):
    category: str

@router.patch("/{session_id}/transactions/{tx_id}")
def api_override_category(
    session_id: str, 
    tx_id: str, 
    payload: OverrideCategorySchema, 
    db: Session = Depends(get_db)
):
    """
    Manually overrides a transaction's category. 
    Learns a new rule for the session, and re-applies it to all matching transactions in the session.
    """
    import uuid
    from models.transaction import Category
    
    # 1. Validate Category name (casing matches enum)
    category_enum_val = None
    for cat in Category:
        if cat.value.lower() == payload.category.lower().strip():
            category_enum_val = cat.value
            break
            
    if not category_enum_val:
        valid_cats = [cat.value for cat in Category]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category '{payload.category}'. Must be one of: {', '.join(valid_cats)}"
        )
        
    # 2. Fetch the transaction to override
    tx = db.query(DBTransaction).filter(
        DBTransaction.session_id == session_id,
        DBTransaction.id == tx_id
    ).first()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found in this session")
        
    # 3. Update the target transaction
    tx.category = category_enum_val
    tx.category_confidence = 1.0
    tx.category_source = "user"
    
    # 4. Session rule learning:
    # Pattern to match: use merchant name if present, otherwise clean description
    pattern = tx.merchant if tx.merchant else tx.clean_description
    pattern_clean = pattern.lower().strip() if pattern else ""
    
    updated_count = 1
    
    if pattern_clean:
        # Check if rule already exists for this session and pattern
        existing_rule = db.query(DBSessionRule).filter(
            DBSessionRule.session_id == session_id,
            DBSessionRule.pattern == pattern_clean
        ).first()
        
        if existing_rule:
            existing_rule.category = category_enum_val
        else:
            db_rule = DBSessionRule(
                id=str(uuid.uuid4()),
                session_id=session_id,
                pattern=pattern_clean,
                category=category_enum_val
            )
            db.add(db_rule)
            
        # Re-apply learned rule to other transactions in this session
        # We match transactions where the merchant or clean_description contains the pattern
        # AND which haven't been manually overridden by the user already (source != 'user')
        other_txs = db.query(DBTransaction).filter(
            DBTransaction.session_id == session_id,
            DBTransaction.id != tx_id,
            DBTransaction.category_source != "user"
        ).all()
        
        for other in other_txs:
            other_merchant_lower = other.merchant.lower().strip() if other.merchant else ""
            other_desc_lower = other.clean_description.lower().strip()
            
            if (pattern_clean == other_merchant_lower) or (pattern_clean in other_desc_lower) or (other_merchant_lower and pattern_clean in other_merchant_lower):
                other.category = category_enum_val
                other.category_confidence = 1.0
                other.category_source = "user"
                updated_count += 1
                
    db.commit()
    
    return {
        "status": "success",
        "message": f"Category updated to '{category_enum_val}'. Learned rule for pattern '{pattern}' and updated {updated_count} transactions.",
        "transactionId": tx_id,
        "updatedCount": updated_count
    }

# Phase 3 imports (json already imported at top — BUG-06 fix)

class RecurringTransactionResponseSchema(BaseModel):
    id: str
    date: str
    rawDescription: str
    cleanDescription: str
    merchant: Optional[str]
    amount: float
    type: str
    category: str

class RecurringGroupResponseSchema(BaseModel):
    groupId: str
    merchant: Optional[str]
    description: str
    amount: float
    frequency: str
    type: str
    transactions: List[RecurringTransactionResponseSchema]

class BiggestTransactionResponseSchema(BaseModel):
    id: str
    date: str
    description: str
    merchant: Optional[str]
    amount: float
    category: str

class TopCategoryResponseSchema(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyAggregationResponseSchema(BaseModel):
    month: str
    income: float
    spend: float

class SummaryResponseSchema(BaseModel):
    income: float
    spend: float
    savings: float
    savingsRate: float
    biggestTransaction: Optional[BiggestTransactionResponseSchema]
    topCategories: List[TopCategoryResponseSchema]
    monthlyAggregation: List[MonthlyAggregationResponseSchema]
    recurringTotal: float

class InsightResponseSchema(BaseModel):
    id: str
    type: str
    title: str
    text: str
    amount: Optional[float]
    relevance: float

@router.get("/{session_id}/recurring", response_model=List[RecurringGroupResponseSchema])
def api_get_recurring(session_id: str, db: Session = Depends(get_db)):
    """Retrieve recurring transaction groups for this session."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    transactions = db.query(DBTransaction).filter(
        DBTransaction.session_id == session_id,
        DBTransaction.is_recurring == True
    ).all()
    
    # Group transactions by recurring_group_id
    groups = {}
    for tx in transactions:
        group_id = tx.recurring_group_id
        if not group_id:
            continue
            
        if group_id not in groups:
            groups[group_id] = []
        groups[group_id].append(tx)
        
    response = []
    for group_id, tx_list in groups.items():
        # Sort chronologically
        tx_list = sorted(tx_list, key=lambda x: x.date)
        
        # Load frequency & type from metadata_json of the first transaction
        frequency = "monthly"
        rec_type = "other"
        avg_amount = 0.0
        
        if tx_list[0].metadata_json:
            try:
                meta = json.loads(tx_list[0].metadata_json)
                rec_meta = meta.get("recurring", {})
                frequency = rec_meta.get("frequency", "monthly")
                rec_type = rec_meta.get("type", "other")
                avg_amount = rec_meta.get("avgAmount", abs(tx_list[0].amount))
            except Exception:
                pass
                
        if avg_amount == 0.0:
            avg_amount = sum(abs(tx.amount) for tx in tx_list) / len(tx_list)
            
        response.append({
            "groupId": group_id,
            "merchant": tx_list[0].merchant,
            "description": tx_list[0].clean_description or tx_list[0].raw_description,
            "amount": round(avg_amount, 2),
            "frequency": frequency,
            "type": rec_type,
            "transactions": [
                {
                    "id": tx.id,
                    "date": tx.date,
                    "rawDescription": tx.raw_description,
                    "cleanDescription": tx.clean_description,
                    "merchant": tx.merchant,
                    "amount": tx.amount,
                    "type": tx.type,
                    "category": tx.category
                } for tx in tx_list
            ]
        })
        
    # GAP-05: Return explanation message when recurring list is empty (REC-01)
    if not response:
        return []

    return response

@router.get("/{session_id}/summary", response_model=SummaryResponseSchema)
def api_get_summary(
    session_id: str,
    fromDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    toDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Retrieve financial summary metrics for this session, optionally filtered by date range."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = db.query(DBTransaction).filter(DBTransaction.session_id == session_id)
    
    if fromDate:
        query = query.filter(DBTransaction.date >= fromDate)
    if toDate:
        query = query.filter(DBTransaction.date <= toDate)
        
    transactions = query.all()
    
    from services.metrics.calculator import MetricsCalculator
    calculator = MetricsCalculator()
    summary = calculator.calculate_metrics(transactions)
    
    return summary

@router.get("/{session_id}/insights", response_model=List[InsightResponseSchema])
def api_get_insights(
    session_id: str,
    fromDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    toDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Retrieve ranked financial insights for this session."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = db.query(DBTransaction).filter(DBTransaction.session_id == session_id)
    if fromDate:
        query = query.filter(DBTransaction.date >= fromDate)
    if toDate:
        query = query.filter(DBTransaction.date <= toDate)
        
    transactions = query.all()
    
    from services.metrics.calculator import MetricsCalculator
    calculator = MetricsCalculator()
    summary = calculator.calculate_metrics(transactions)
    
    from services.insights.generator import InsightsGenerator
    generator = InsightsGenerator()
    insights = generator.generate_insights(summary)
    
    return insights

@router.get("/{session_id}/report")
def api_get_report(
    session_id: str,
    format: str = Query(default="html"),
    fromDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    toDate: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db)
):
    """Retrieve a printable standalone HTML report or download a PDF report for this session."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = db.query(DBTransaction).filter(DBTransaction.session_id == session_id)
    if fromDate:
        query = query.filter(DBTransaction.date >= fromDate)
    if toDate:
        query = query.filter(DBTransaction.date <= toDate)
        
    transactions = query.all()
    
    from services.metrics.calculator import MetricsCalculator
    calculator = MetricsCalculator()
    summary = calculator.calculate_metrics(transactions)
    
    from services.insights.generator import InsightsGenerator
    generator = InsightsGenerator()
    insights = generator.generate_insights(summary)
    
    from services.report.generator import generate_html_report
    html_content = generate_html_report(session_id, summary, transactions, insights, fromDate, toDate)
    
    if format.lower() == "pdf":
        from services.report.generator import generate_pdf_report
        from fastapi import Response
        try:
            pdf_bytes = generate_pdf_report(html_content)
            headers = {
                "Content-Disposition": f'attachment; filename="report-{session_id[:8]}.pdf"'
            }
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
            
    return HTMLResponse(content=html_content)
