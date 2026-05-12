# src/pii/anonymizer.py
import pandas as pd
import hashlib
import re
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii, RecognizerResult

fake = Faker("vi_VN")
Faker.seed(42)

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # Sort by start position descending to replace from end first
        results = sorted(results, key=lambda x: x.start, reverse=True)
        
        anonymized = text
        
        for result in results:
            entity_type = result.entity_type
            original_value = text[result.start:result.end]
            
            if strategy == "replace":
                if entity_type == "PERSON":
                    new_value = fake.name()
                elif entity_type == "EMAIL_ADDRESS":
                    new_value = fake.email()
                elif entity_type == "VN_CCCD":
                    new_value = fake.bothify(text="############")
                elif entity_type == "VN_PHONE":
                    new_value = fake.phone_number()
                else:
                    new_value = "[REDACTED]"
            elif strategy == "mask":
                if entity_type == "PERSON":
                    parts = original_value.split()
                    new_value = " ".join([p[0] + "*" * (len(p) - 1) for p in parts])
                elif entity_type in ["VN_CCCD", "VN_PHONE"]:
                    new_value = original_value[:3] + "*" * (len(original_value) - 3)
                elif entity_type == "EMAIL_ADDRESS":
                    parts = original_value.split("@")
                    new_value = parts[0][:2] + "*" * (len(parts[0]) - 2) + "@" + parts[1]
                else:
                    new_value = "*" * len(original_value)
            elif strategy == "hash":
                new_value = hashlib.sha256(original_value.encode()).hexdigest()[:16]
            else:
                new_value = "[REDACTED]"
            
            # Replace in text
            anonymized = anonymized[:result.start] + new_value + anonymized[result.end:]
        
        return anonymized

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # ho_ten: anonymize bằng anonymize_text
        df_anon["ho_ten"] = df_anon["ho_ten"].apply(lambda x: self.anonymize_text(str(x), "replace"))
        
        # dia_chi: anonymize bằng anonymize_text  
        df_anon["dia_chi"] = df_anon["dia_chi"].apply(lambda x: self.anonymize_text(str(x), "replace"))
        
        # email: anonymize bằng anonymize_text
        df_anon["email"] = df_anon["email"].apply(lambda x: self.anonymize_text(str(x), "replace"))
        
        # cccd: replace trực tiếp bằng fake CCCD (11-12 random digits)
        df_anon["cccd"] = [fake.bothify(text="############") for _ in range(len(df_anon))]
        
        # so_dien_thoai: replace trực tiếp bằng fake phone (format VN)
        def generate_vn_phone():
            prefix = fake.random_element(['03', '05', '07', '08', '09'])
            number = fake.numerify(text='########')
            return prefix + number
        df_anon["so_dien_thoai"] = [generate_vn_phone() for _ in range(len(df_anon))]
        
        # bac_si_phu_trach: anonymize bằng anonymize_text
        df_anon["bac_si_phu_trach"] = df_anon["bac_si_phu_trach"].apply(lambda x: self.anonymize_text(str(x), "replace"))

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
