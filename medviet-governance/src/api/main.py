# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    # Check permission first
    from src.access.rbac import enforcer
    role = current_user["role"]
    if not enforcer.enforce(role, "patient_data", "read"):
        raise HTTPException(status_code=403, detail=f"Role '{role}' cannot access raw patient data")
    
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        return {"data": df.head(10).to_dict(orient="records")}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found")

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    from src.access.rbac import enforcer
    role = current_user["role"]
    if not enforcer.enforce(role, "training_data", "read"):
        raise HTTPException(status_code=403, detail=f"Role '{role}' cannot access training data")
    
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        df_anon = anonymizer.anonymize_dataframe(df)
        return {"data": df_anon.to_dict(orient="records")}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found")

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    from src.access.rbac import enforcer
    role = current_user["role"]
    if not enforcer.enforce(role, "aggregated_metrics", "read"):
        raise HTTPException(status_code=403, detail=f"Role '{role}' cannot access aggregated metrics")
    
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        # Aggregate by disease type
        metrics = df.groupby("benh").agg({
            "patient_id": "count",
            "ket_qua_xet_nghiem": ["mean", "min", "max"]
        }).to_dict()
        
        return {
            "data": {
                "total_patients": len(df),
                "by_disease": metrics["patient_id"]["count"] if isinstance(metrics["patient_id"], dict) else dict(df.groupby("benh")["patient_id"].count()),
                "test_results_stats": {
                    "mean": df["ket_qua_xet_nghiem"].mean(),
                    "min": df["ket_qua_xet_nghiem"].min(),
                    "max": df["ket_qua_xet_nghiem"].max()
                }
            }
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient data not found")

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    from src.access.rbac import enforcer
    role = current_user["role"]
    if not enforcer.enforce(role, "patient_data", "delete"):
        raise HTTPException(status_code=403, detail=f"Role '{role}' cannot delete patient data")
    
    return {"message": f"Patient {patient_id} deleted", "deleted_by": current_user["username"]}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
