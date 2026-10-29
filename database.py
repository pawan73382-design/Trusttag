"""
TrustTag - Anti-Counterfeit Trust Layer
Database Layer & SQLite Persistence (database.py)
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "trusttag.db")
SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_data.json")


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_path: str = SEED_FILE, force_reset: bool = False) -> None:
    """Initializes tables and seeds data if empty or forced."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_reset:
        cursor.execute("DROP TABLE IF EXISTS complaints;")
        cursor.execute("DROP TABLE IF EXISTS disputes;")
        cursor.execute("DROP TABLE IF EXISTS seller_verifications;")
        cursor.execute("DROP TABLE IF EXISTS products;")
        cursor.execute("DROP TABLE IF EXISTS manufacturer_registry;")
        cursor.execute("DROP TABLE IF EXISTS sellers;")
        cursor.execute("DROP TABLE IF EXISTS market_baselines;")

    # 1. Sellers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            account_age_months INTEGER NOT NULL,
            is_id_verified BOOLEAN NOT NULL DEFAULT 0,
            is_business_registered BOOLEAN NOT NULL DEFAULT 0,
            business_registration_number TEXT,
            total_orders INTEGER NOT NULL DEFAULT 0,
            total_complaints INTEGER NOT NULL DEFAULT 0,
            avg_response_hours REAL NOT NULL DEFAULT 24.0,
            contact_reachable BOOLEAN NOT NULL DEFAULT 1,
            support_email TEXT,
            support_phone TEXT,
            badge_status TEXT NOT NULL DEFAULT 'CAUTION',
            notes TEXT
        );
    """)

    # 2. Manufacturer Registry (Ground-truth authenticity ledger)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manufacturer_registry (
            serial_number TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            authorized_batch TEXT NOT NULL,
            msrp REAL NOT NULL,
            is_genuine BOOLEAN NOT NULL DEFAULT 1,
            registered_manufacturer TEXT NOT NULL,
            packaging_signature TEXT,
            safety_certifications TEXT
        );
    """)

    # 3. Products listed by sellers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            serial_number TEXT NOT NULL,
            batch_code TEXT NOT NULL,
            seller_id TEXT NOT NULL,
            category TEXT NOT NULL,
            listed_price REAL NOT NULL,
            packaging_claimed TEXT,
            is_flagged BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );
    """)

    # 4. Complaints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL,
            product_serial TEXT,
            batch_code TEXT,
            buyer_name TEXT NOT NULL,
            buyer_email TEXT NOT NULL,
            purchase_price REAL,
            days_before_failure INTEGER,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence_urls TEXT,
            seller_responded BOOLEAN NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'SUBMITTED',
            date_filed TEXT NOT NULL,
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        );
    """)

    # 5. Disputes & Resolutions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disputes (
            id TEXT PRIMARY KEY,
            complaint_id TEXT NOT NULL,
            classification TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            seller_action_required TEXT,
            buyer_message_draft TEXT,
            seller_message_draft TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        );
    """)

    # 6. Seller Verifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seller_verifications (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL,
            business_name TEXT NOT NULL,
            tax_id TEXT,
            id_document_type TEXT,
            contact_email TEXT NOT NULL,
            phone TEXT,
            verified_badge_awarded BOOLEAN NOT NULL DEFAULT 0,
            verification_score INTEGER NOT NULL,
            remarks TEXT,
            created_at TEXT NOT NULL
        );
    """)

    # 7. Market Baselines
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_baselines (
            category_key TEXT PRIMARY KEY,
            category_name TEXT NOT NULL,
            average_price REAL NOT NULL,
            minimum_legit_price REAL NOT NULL,
            typical_margin_alert_threshold REAL NOT NULL
        );
    """)

    conn.commit()

    # Seed if tables are empty
    cursor.execute("SELECT COUNT(*) FROM sellers;")
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Insert market baselines
        for cat_key, cat_data in data.get("market_baselines", {}).items():
            cursor.execute("""
                INSERT OR REPLACE INTO market_baselines 
                (category_key, category_name, average_price, minimum_legit_price, typical_margin_alert_threshold)
                VALUES (?, ?, ?, ?, ?);
            """, (
                cat_key,
                cat_data.get("category", cat_key),
                cat_data.get("average_price", 0.0),
                cat_data.get("minimum_legit_price", 0.0),
                cat_data.get("typical_margin_alert_threshold", 0.5)
            ))

        # Insert sellers
        for s in data.get("sellers", []):
            cursor.execute("""
                INSERT OR REPLACE INTO sellers
                (id, name, account_age_months, is_id_verified, is_business_registered,
                 business_registration_number, total_orders, total_complaints,
                 avg_response_hours, contact_reachable, support_email, support_phone,
                 badge_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                s["id"], s["name"], s["account_age_months"],
                1 if s["is_id_verified"] else 0,
                1 if s["is_business_registered"] else 0,
                s.get("business_registration_number"),
                s["total_orders"], s["total_complaints"],
                s["avg_response_hours"],
                1 if s["contact_reachable"] else 0,
                s.get("support_email"), s.get("support_phone"),
                s["badge_status"], s.get("notes")
            ))

        # Insert manufacturer registry
        for m in data.get("manufacturer_registry", []):
            cert_str = json.dumps(m.get("safety_certifications", []))
            cursor.execute("""
                INSERT OR REPLACE INTO manufacturer_registry
                (serial_number, product_name, category, brand, authorized_batch, msrp,
                 is_genuine, registered_manufacturer, packaging_signature, safety_certifications)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                m["serial_number"], m["product_name"], m["category"], m["brand"],
                m["authorized_batch"], m["msrp"],
                1 if m["is_genuine"] else 0,
                m["registered_manufacturer"],
                m.get("packaging_signature"),
                cert_str
            ))

        # Insert products
        for p in data.get("products", []):
            cursor.execute("""
                INSERT OR REPLACE INTO products
                (id, name, serial_number, batch_code, seller_id, category, listed_price,
                 packaging_claimed, is_flagged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                p["id"], p["name"], p["serial_number"], p["batch_code"], p["seller_id"],
                p["category"], p["listed_price"], p.get("packaging_claimed"),
                1 if p["is_flagged"] else 0
            ))

        # Insert complaints
        for c in data.get("complaints", []):
            evidence_str = json.dumps(c.get("evidence_urls", []))
            cursor.execute("""
                INSERT OR REPLACE INTO complaints
                (id, seller_id, product_serial, batch_code, buyer_name, buyer_email,
                 purchase_price, days_before_failure, category, title, description,
                 evidence_urls, seller_responded, status, date_filed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                c["id"], c["seller_id"], c.get("product_serial"), c.get("batch_code"),
                c["buyer_name"], c["buyer_email"], c.get("purchase_price"),
                c.get("days_before_failure"), c["category"], c["title"], c["description"],
                evidence_str, 1 if c.get("seller_responded") else 0,
                c.get("status", "SUBMITTED"), c.get("date_filed", "2024-10-28")
            ))

        conn.commit()

    conn.close()


# Database query helpers
def get_seller_by_id_or_name(query: str) -> Optional[Dict[str, Any]]:
    """Looks up seller by exact ID or case-insensitive partial name match."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sellers 
        WHERE LOWER(id) = LOWER(?) OR LOWER(name) = LOWER(?) OR LOWER(name) LIKE ?
        LIMIT 1;
    """, (query.strip(), query.strip(), f"%{query.strip().lower()}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_sellers() -> List[Dict[str, Any]]:
    """Retrieves all registered sellers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sellers ORDER BY account_age_months DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_manufacturer_registry_entry(serial_or_qr: str) -> Optional[Dict[str, Any]]:
    """Looks up product in the manufacturer registry by serial or QR string."""
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_serial = serial_or_qr.strip()
    cursor.execute("""
        SELECT * FROM manufacturer_registry 
        WHERE LOWER(serial_number) = LOWER(?)
        LIMIT 1;
    """, (clean_serial,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["safety_certifications"] = json.loads(d.get("safety_certifications") or "[]")
        except Exception:
            d["safety_certifications"] = []
        return d
    return None


def get_market_baseline(category: str) -> Optional[Dict[str, Any]]:
    """Fetches baseline price metrics for a given category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM market_baselines 
        WHERE LOWER(category_key) = LOWER(?) OR LOWER(category_name) LIKE ?
        LIMIT 1;
    """, (category.strip(), f"%{category.strip().lower()}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_market_baselines() -> Dict[str, Dict[str, Any]]:
    """Returns all category market baselines."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_baselines;")
    rows = cursor.fetchall()
    conn.close()
    return {r["category_key"]: dict(r) for r in rows}


def get_complaints_for_seller(seller_id: str) -> List[Dict[str, Any]]:
    """Fetches all complaints for a given seller ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE seller_id = ? 
        ORDER BY date_filed DESC;
    """, (seller_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_complaints_for_batch(batch_code: str) -> List[Dict[str, Any]]:
    """Fetches all complaints for a given batch code."""
    if not batch_code:
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE LOWER(batch_code) = LOWER(?) 
        ORDER BY date_filed DESC;
    """, (batch_code.strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_complaints_for_serial(serial_number: str) -> List[Dict[str, Any]]:
    """Fetches complaints matching a specific serial number."""
    if not serial_number:
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM complaints 
        WHERE LOWER(product_serial) = LOWER(?) 
        ORDER BY date_filed DESC;
    """, (serial_number.strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_complaints(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches recent complaints across all sellers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, s.name as seller_name, s.badge_status as seller_badge
        FROM complaints c
        LEFT JOIN sellers s ON c.seller_id = s.id
        ORDER BY c.date_filed DESC
        LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_complaint(c: Dict[str, Any]) -> str:
    """Inserts a new complaint and updates seller complaint count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate ID if missing
    complaint_id = c.get("id") or f"CMP-{int(sqlite3.time.time())}"
    evidence_str = json.dumps(c.get("evidence_urls", []))
    
    cursor.execute("""
        INSERT INTO complaints
        (id, seller_id, product_serial, batch_code, buyer_name, buyer_email,
         purchase_price, days_before_failure, category, title, description,
         evidence_urls, seller_responded, status, date_filed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        complaint_id, c["seller_id"], c.get("product_serial"), c.get("batch_code"),
        c["buyer_name"], c["buyer_email"], c.get("purchase_price", 0.0),
        c.get("days_before_failure", 0), c.get("category", "counterfeit"),
        c["title"], c["description"], evidence_str,
        1 if c.get("seller_responded") else 0,
        c.get("status", "SUBMITTED"), c.get("date_filed", "2026-10-28")
    ))

    # Increment complaint counter on seller
    cursor.execute("""
        UPDATE sellers 
        SET total_complaints = total_complaints + 1 
        WHERE id = ?;
    """, (c["seller_id"],))

    conn.commit()
    conn.close()
    return complaint_id


def insert_dispute(d: Dict[str, Any]) -> str:
    """Inserts dispute recommendation record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    dispute_id = d.get("id") or f"DSP-{int(sqlite3.time.time())}"
    cursor.execute("""
        INSERT INTO disputes
        (id, complaint_id, classification, recommended_action, seller_action_required,
         buyer_message_draft, seller_message_draft, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        dispute_id, d["complaint_id"], d["classification"],
        d["recommended_action"], d.get("seller_action_required", ""),
        d.get("buyer_message_draft", ""), d.get("seller_message_draft", ""),
        d.get("created_at", "2026-10-28")
    ))
    conn.commit()
    conn.close()
    return dispute_id


def save_seller_verification(v: Dict[str, Any]) -> Dict[str, Any]:
    """Records seller verification submission and updates badge if passing score."""
    conn = get_db_connection()
    cursor = conn.cursor()
    verif_id = f"VRF-{int(sqlite3.time.time())}"
    score = v.get("verification_score", 0)
    awarded = score >= 75
    badge = "VERIFIED" if awarded else ("CAUTION" if score >= 50 else "HIGH_RISK")

    cursor.execute("""
        INSERT INTO seller_verifications
        (id, seller_id, business_name, tax_id, id_document_type, contact_email,
         phone, verified_badge_awarded, verification_score, remarks, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        verif_id, v["seller_id"], v["business_name"], v.get("tax_id"),
        v.get("id_document_type"), v["contact_email"], v.get("phone"),
        1 if awarded else 0, score, v.get("remarks", ""),
        v.get("created_at", "2026-10-28")
    ))

    # Update seller record
    cursor.execute("""
        UPDATE sellers 
        SET is_id_verified = 1,
            is_business_registered = ?,
            business_registration_number = COALESCE(?, business_registration_number),
            badge_status = ?,
            support_email = COALESCE(?, support_email),
            support_phone = COALESCE(?, support_phone),
            contact_reachable = 1
        WHERE id = ?;
    """, (
        1 if v.get("tax_id") else 0,
        v.get("tax_id"),
        badge,
        v.get("contact_email"),
        v.get("phone"),
        v["seller_id"]
    ))

    conn.commit()
    conn.close()
    return {
        "verification_id": verif_id,
        "badge_awarded": awarded,
        "badge_status": badge,
        "score": score
    }


def find_complaint_clusters(min_reports: int = 3, max_days_threshold: int = 7) -> List[Dict[str, Any]]:
    """
    Detects scam clusters across buyers by:
    - Same seller + same batch code
    - Multiple failure reports within <= 7 days
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            c.seller_id,
            s.name as seller_name,
            s.badge_status,
            c.batch_code,
            c.product_serial,
            COUNT(c.id) as report_count,
            SUM(CASE WHEN c.days_before_failure <= ? THEN 1 ELSE 0 END) as rapid_failures,
            AVG(c.days_before_failure) as avg_days_to_fail,
            SUM(CASE WHEN c.seller_responded = 0 THEN 1 ELSE 0 END) as ghosted_buyers
        FROM complaints c
        JOIN sellers s ON c.seller_id = s.id
        WHERE c.batch_code IS NOT NULL AND c.batch_code != ''
        GROUP BY c.seller_id, c.batch_code
        HAVING COUNT(c.id) >= ?
        ORDER BY report_count DESC;
    """, (max_days_threshold, min_reports))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    print("Initializing TrustTag SQLite Database...")
    init_db(force_reset=True)
    print("Database initialized successfully at:", DB_FILE)
    sellers = get_all_sellers()
    print(f"Loaded {len(sellers)} sellers.")
    clusters = find_complaint_clusters()
    print(f"Detected {len(clusters)} complaint cluster(s).")
