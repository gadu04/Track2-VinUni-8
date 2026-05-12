# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | CloudTrail + API access logs | ✅ Done | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus) | ✅ Done | Security Team |

## F. Technical Solutions cho các phần Todo

### Audit Logging (CloudTrail + API access logs)
**Technical Solution:**
- Implement FastAPI middleware để log tất cả API requests
- Lưu log vào file `logs/access.log` với format: timestamp, user, action, resource, status
- CloudTrail integration: forward logs sang AWS CloudWatch
- Cấu hình log retention 90 ngày theo NĐ13

**Implementation:**
```python
# src/middleware/audit_logging.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")
audit_logger.info(f"{datetime.now()}, {user}, {action}, {resource}, {status}")
```

### Breach Detection (Anomaly monitoring - Prometheus)
**Technical Solution:**
- Sử dụng Prometheus metrics để track suspicious activities:
  - Số lượng failed login attempts
  - Số lượng API calls bất thường
  - Memory/CPU usage spikes
- Cấu hình Prometheus AlertManager để gửi alert khi:
  - > 10 failed logins trong 5 phút
  - > 1000 API requests từ 1 user trong 1 phút
- Alert được gửi qua email tới security team

**Implementation:**
```python
# Metrics endpoint
@app.get("/metrics")
def metrics():
    return {
        "failed_logins": failed_login_counter,
        "api_requests": api_request_counter,
        "anomalies": anomaly_detector.get_anomalies()
    }
```
