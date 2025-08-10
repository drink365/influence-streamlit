import json
from datetime import datetime
from src.db import get_conn

class CaseRepo:
    TBL = "cases"

    @staticmethod
    def upsert(case: dict):
        conn = get_conn()
        now = datetime.utcnow().isoformat()
        case = {**case}
        case.setdefault("created_at", now)
        case["updated_at"] = now
        payload_json = json.dumps(case.get("payload", {}), ensure_ascii=False)
        conn.execute(
            f"""
            INSERT INTO {CaseRepo.TBL} (
              id, advisor_id, advisor_name, client_alias,
              assets_financial, assets_realestate, assets_business,
              liabilities, net_estate, tax_estimate, liquidity_needed,
              status, payload_json, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              advisor_id=excluded.advisor_id,
              advisor_name=excluded.advisor_name,
              client_alias=excluded.client_alias,
              assets_financial=excluded.assets_financial,
              assets_realestate=excluded.assets_realestate,
              assets_business=excluded.assets_business,
              liabilities=excluded.liabilities,
              net_estate=excluded.net_estate,
              tax_estimate=excluded.tax_estimate,
              liquidity_needed=excluded.liquidity_needed,
              status=excluded.status,
              payload_json=excluded.payload_json,
              updated_at=excluded.updated_at
            """,
            (
                case["id"], case.get("advisor_id"), case.get("advisor_name"), case.get("client_alias"),
                case.get("assets_financial",0), case.get("assets_realestate",0), case.get("assets_business",0),
                case.get("liabilities",0), case.get("net_estate",0), case.get("tax_estimate",0), case.get("liquidity_needed",0),
                case.get("status","Prospect"), payload_json, case.get("created_at"), case.get("updated_at"),
            ),
        )
        conn.commit()

    @staticmethod
    def get(case_id: str):
        cur = get_conn().execute(f"SELECT * FROM {CaseRepo.TBL} WHERE id=?", (case_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_status(case_id: str, status: str):
        get_conn().execute(
            f"UPDATE {CaseRepo.TBL} SET status=?, updated_at=? WHERE id=?",
            (status, datetime.utcnow().isoformat(), case_id),
        ).connection.commit()
