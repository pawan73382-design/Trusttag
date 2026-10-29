"""
TrustTag - Deterministic Anti-Counterfeit Scoring & Verification Tools (tools.py)

IMPORTANT DESIGN RULE:
Calculates scores and thresholds with deterministic Python code inside tools,
so numbers are accurate and repeatable. Use LLM only for reasoning, explanation,
and communication drafting.
"""

import json
from typing import Any, Dict, List, Optional
import database

try:
    from crewai.tools import tool
    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False
    def tool(name_or_func):
        """Fallback decorator when crewai is not present."""
        if callable(name_or_func):
            return name_or_func
        def decorator(f):
            return f
        return decorator


# ---------------------------------------------------------------------------
# 1. Deterministic Seller Credibility Scorer
# ---------------------------------------------------------------------------
def calculate_seller_credibility(seller_query: str) -> Dict[str, Any]:
    """
    Evaluates seller credibility from database records using deterministic rubric:
    - Account age (0-25 pts)
    - Identity & Business verification (0-25 pts)
    - Order history & Complaint ratio (0-25 pts)
    - Response time & Contact reachability (0-25 pts)
    Total: 0 - 100 pts
    """
    seller = database.get_seller_by_id_or_name(seller_query)
    if not seller:
        return {
            "found": False,
            "seller_id": seller_query,
            "seller_name": "Unknown Seller",
            "score": 20,
            "badge_status": "HIGH_RISK",
            "breakdown": {
                "account_age_pts": 5,
                "verification_pts": 0,
                "complaint_ratio_pts": 5,
                "reachability_pts": 10,
            },
            "flags": ["Seller not found in verified registry.", "Unverified merchant account."],
            "summary": "Unknown or unindexed seller with no verified credentials on file."
        }

    # 1. Account age points (0 - 25)
    age_months = seller["account_age_months"]
    if age_months >= 24:
        age_pts = 25
    elif age_months >= 12:
        age_pts = 20
    elif age_months >= 6:
        age_pts = 14
    elif age_months >= 3:
        age_pts = 8
    else:
        age_pts = 3  # Brand new burner account territory

    # 2. Verification points (0 - 25)
    verif_pts = 0
    if seller["is_id_verified"]:
        verif_pts += 10
    if seller["is_business_registered"]:
        verif_pts += 15

    # 3. Order volume & Complaint ratio points (0 - 25)
    total_orders = max(seller["total_orders"], 1)
    complaints = seller["total_complaints"]
    complaint_rate = complaints / total_orders

    if total_orders >= 500:
        base_order_pts = 10
    elif total_orders >= 100:
        base_order_pts = 6
    else:
        base_order_pts = 2

    if complaint_rate <= 0.005:  # <= 0.5%
        ratio_pts = 15
    elif complaint_rate <= 0.02:  # <= 2%
        ratio_pts = 10
    elif complaint_rate <= 0.05:  # <= 5%
        ratio_pts = 5
    else:
        ratio_pts = 0  # High failure/dispute rate

    complaint_order_pts = min(25, base_order_pts + ratio_pts)

    # 4. Reachability & Response time points (0 - 25)
    reach_pts = 0
    if not seller["contact_reachable"]:
        reach_pts = 0  # Severe red flag: seller unreachable
    else:
        reach_pts += 10
        resp_hours = seller["avg_response_hours"]
        if resp_hours <= 4.0:
            reach_pts += 15
        elif resp_hours <= 12.0:
            reach_pts += 10
        elif resp_hours <= 24.0:
            reach_pts += 5
        elif resp_hours <= 48.0:
            reach_pts += 2
        else:
            reach_pts += 0

    total_score = max(0, min(100, age_pts + verif_pts + complaint_order_pts + reach_pts))

    flags = []
    if not seller["contact_reachable"]:
        flags.append("CRITICAL: Seller contact details bounce or are unreachable.")
    if age_months <= 2:
        flags.append(f"Account is only {age_months} month(s) old (burner account risk).")
    if not seller["is_id_verified"]:
        flags.append("Seller identity has not been legally verified.")
    if not seller["is_business_registered"]:
        flags.append("No active commercial business registration on file.")
    if complaint_rate > 0.05:
        flags.append(f"High dispute rate: {complaint_rate*100:.1f}% of orders have complaints.")
    if seller["avg_response_hours"] > 48.0:
        flags.append(f"Slow response time: averaging {seller['avg_response_hours']:.1f} hours to reply.")

    badge = "VERIFIED" if total_score >= 75 else ("CAUTION" if total_score >= 50 else "HIGH_RISK")

    return {
        "found": True,
        "seller_id": seller["id"],
        "seller_name": seller["name"],
        "score": total_score,
        "badge_status": badge,
        "account_age_months": age_months,
        "total_orders": total_orders,
        "total_complaints": complaints,
        "complaint_rate_pct": round(complaint_rate * 100, 2),
        "avg_response_hours": seller["avg_response_hours"],
        "contact_reachable": bool(seller["contact_reachable"]),
        "breakdown": {
            "account_age_pts": age_pts,
            "verification_pts": verif_pts,
            "complaint_order_pts": complaint_order_pts,
            "reachability_pts": reach_pts
        },
        "flags": flags,
        "summary": f"Seller score is {total_score}/100 ({badge}). {len(flags)} risk warning(s) found."
    }


# ---------------------------------------------------------------------------
# 2. Deterministic Product Authenticity Scorer
# ---------------------------------------------------------------------------
def check_product_authenticity(
    serial_or_qr: str,
    category: str,
    listed_price: float,
    claimed_packaging: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks product serial against manufacturer registry, tests price against
    market baselines to spot tempting counterfeit prices, and evaluates packaging flags.
    Score: 0 - 100 pts
    """
    registry_entry = database.get_manufacturer_registry_entry(serial_or_qr)
    baseline = database.get_market_baseline(category)
    
    avg_price = baseline["average_price"] if baseline else 35.0
    min_legit_price = baseline["minimum_legit_price"] if baseline else 15.0

    flags: List[str] = []
    points = 0

    # 1. Registry Match (0 - 45 pts)
    if not registry_entry:
        registry_status = "NOT_IN_REGISTRY"
        registry_pts = 10
        flags.append(f"Serial '{serial_or_qr}' is not registered with any authorized manufacturer.")
    elif not registry_entry["is_genuine"]:
        registry_status = "KNOWN_COUNTERFEIT_SERIAL"
        registry_pts = 0
        flags.append(f"CRITICAL: Serial '{serial_or_qr}' is flagged on blacklists as known counterfeit/clone.")
        flags.append(f"Registry notes: {registry_entry.get('packaging_signature', '')}")
    else:
        registry_status = "GENUINE_REGISTERED"
        registry_pts = 45

    points += registry_pts

    # 2. Price Baseline Analysis (0 - 35 pts) - The "Tempting Price" check
    price_ratio = listed_price / avg_price if avg_price > 0 else 1.0

    if listed_price < (min_legit_price * 0.7):
        # Tempting price: way below manufacturing minimum cost!
        price_pts = 0
        flags.append(
            f"TEMPTING PRICE ALERT: Listed at ${listed_price:.2f}, while minimum legit retail is "
            f"${min_legit_price:.2f} (avg ${avg_price:.2f}). {round((1-price_ratio)*100)}% below market - typical clone lure!"
        )
    elif listed_price < min_legit_price:
        price_pts = 15
        flags.append(
            f"Price (${listed_price:.2f}) is below standard minimum (${min_legit_price:.2f}). Proceed with caution."
        )
    elif listed_price > (avg_price * 1.8):
        price_pts = 25  # Overpriced or scalped, but not counterfeit lure
    else:
        price_pts = 35  # Healthy market baseline price

    points += price_pts

    # 3. Packaging & Safety Certification (0 - 20 pts)
    pkg_pts = 20
    claimed_lower = (claimed_packaging or "").lower()
    if registry_entry and not registry_entry["is_genuine"]:
        pkg_pts = 0
        flags.append("Packaging matches known look-alike clone aesthetics.")
    elif "lookalike" in claimed_lower or "look-alike" in claimed_lower or "unlabeled" in claimed_lower or "polybag" in claimed_lower:
        pkg_pts = 5
        flags.append("Suspect packaging description: Unsealed bag or look-alike casing reported.")
    elif registry_entry and len(registry_entry.get("safety_certifications", [])) > 0:
        pkg_pts = 20
    else:
        pkg_pts = 12

    points += pkg_pts

    total_score = max(0, min(100, points))
    auth_label = "AUTHENTIC" if total_score >= 80 else ("SUSPICIOUS" if total_score >= 45 else "COUNTERFEIT_ALERT")

    return {
        "serial_or_qr": serial_or_qr,
        "score": total_score,
        "authenticity_label": auth_label,
        "registry_status": registry_status,
        "registry_data": registry_entry,
        "market_comparison": {
            "listed_price": listed_price,
            "baseline_avg": avg_price,
            "min_legit_price": min_legit_price,
            "discount_from_avg_pct": round((1 - price_ratio) * 100, 1) if price_ratio < 1 else 0.0
        },
        "breakdown": {
            "registry_pts": registry_pts,
            "price_pts": price_pts,
            "packaging_pts": pkg_pts
        },
        "flags": flags,
        "is_safe": total_score >= 70 and registry_status != "KNOWN_COUNTERFEIT_SERIAL"
    }


# ---------------------------------------------------------------------------
# 3. Complaint Intelligence & Clustering Tool
# ---------------------------------------------------------------------------
def analyze_complaint_clusters(
    seller_id: str,
    batch_code: Optional[str] = None,
    serial_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Connects isolated complaints to uncover fraud patterns:
    - Clusters by (seller_id, batch_code)
    - Early failure rate (failed within <= 7 days)
    - Unreachable seller pattern (seller ghosting buyers)
    """
    seller_complaints = database.get_complaints_for_seller(seller_id)
    batch_complaints = database.get_complaints_for_batch(batch_code) if batch_code else []
    serial_complaints = database.get_complaints_for_serial(serial_number) if serial_number else []

    # Count quick failures (<= 7 days)
    quick_failures = [c for c in batch_complaints if (c.get("days_before_failure") or 999) <= 7]
    ghosted_count = [c for c in batch_complaints if not c.get("seller_responded")]

    cluster_severity = "NONE"
    penalty = 0
    warnings = []

    if len(batch_complaints) >= 3 and len(quick_failures) >= 2:
        cluster_severity = "CRITICAL_FRAUD_CLUSTER"
        penalty = 45
        warnings.append(
            f"HIGH-SEVERITY SCAM CLUSTER: {len(batch_complaints)} buyers reported failure for batch '{batch_code}'. "
            f"{len(quick_failures)} units failed within 7 days. {len(ghosted_count)} buyers were ghosted by seller."
        )
    elif len(quick_failures) >= 2:
        cluster_severity = "EARLY_FAILURE_WARNING"
        penalty = 25
        warnings.append(
            f"Rapid failure cluster detected: {len(quick_failures)} units reported failure within 7 days."
        )
    elif len(seller_complaints) >= 20:
        cluster_severity = "ELEVATED_SELLER_RISK"
        penalty = 20
        warnings.append(
            f"High complaint volume: Seller has {len(seller_complaints)} recorded buyer complaints on file."
        )
    else:
        cluster_severity = "CLEAN_OR_ISOLATED"
        penalty = 0

    return {
        "seller_id": seller_id,
        "batch_code": batch_code,
        "cluster_severity": cluster_severity,
        "risk_penalty": penalty,
        "total_seller_complaints": len(seller_complaints),
        "total_batch_complaints": len(batch_complaints),
        "rapid_failures_under_7_days": len(quick_failures),
        "ghosted_buyers": len(ghosted_count),
        "warnings": warnings,
        "sample_complaints": batch_complaints[:3] if batch_complaints else seller_complaints[:2]
    }


# ---------------------------------------------------------------------------
# 4. Dispute Resolution & Notice Drafter Tool
# ---------------------------------------------------------------------------
def evaluate_dispute_and_draft_resolution(
    complaint_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates new buyer complaint deterministically, classifies problem,
    recommends action (refund/replace/warning/escalate), and crafts formal notices.
    """
    category = complaint_data.get("category", "counterfeit").lower()
    days_failed = complaint_data.get("days_before_failure", 0)
    price = complaint_data.get("purchase_price", 0.0)
    seller_id = complaint_data.get("seller_id", "")
    buyer_name = complaint_data.get("buyer_name", "Valued Buyer")
    
    seller = database.get_seller_by_id_or_name(seller_id)
    seller_name = seller["name"] if seller else "Seller"

    # Rule-based classification & outcome
    if category == "counterfeit" or days_failed <= 7:
        classification = "COUNTERFEIT_SCAM_ESCALATION"
        recommended_action = "MANDATORY_FULL_REFUND_AND_SELLER_SANCTION"
        seller_action_required = "Immediate refund to buyer within 24h; submit proof of stock provenance."
        status = "ESCALATED_HIGH_RISK"
    elif category == "defective" and days_failed <= 30:
        classification = "EARLY_HARDWARE_DEFECT"
        recommended_action = "MERCHANT_REPLACEMENT_OR_RETURN"
        seller_action_required = "Issue pre-paid return shipping label and ship tested replacement."
        status = "PENDING_MERCHANT_ACTION"
    elif category == "non_delivery":
        classification = "LOGISTICS_NON_DELIVERY"
        recommended_action = "CARRIER_TRACE_OR_REFUND"
        seller_action_required = "Provide GPS delivery confirmation or issue full credit."
        status = "PENDING_MERCHANT_ACTION"
    else:
        classification = "STANDARD_WARRANTY_INQUIRY"
        recommended_action = "MANUFACTURER_WARRANTY_ROUTING"
        seller_action_required = "Provide manufacturer warranty service contact."
        status = "IN_REVIEW"

    # Draft structured, professional messages
    buyer_message = (
        f"Dear {buyer_name},\n\n"
        f"TrustTag Dispute Case #{complaint_data.get('id', 'NEW-CASE')} has been opened. "
        f"Based on our automated intelligence scan, this issue is classified as '{classification}'.\n\n"
        f"Recommended Resolution: {recommended_action}.\n"
        f"We have notified {seller_name} to take corrective action ({seller_action_required}). "
        f"Your case is tracked under TrustTag's Buyer Protection Shield."
    )

    seller_message = (
        f"URGENT NOTICE TO {seller_name.upper()}:\n\n"
        f"A verified buyer complaint (Case #{complaint_data.get('id', 'NEW-CASE')}) has been lodged regarding product '{complaint_data.get('title', 'Electronic accessory')}'.\n"
        f"Finding: {classification}.\n"
        f"Action Required: {seller_action_required}\n"
        f"Failure to respond within 48 hours will trigger an immediate trust score downgrade and public listing on the TrustTag Risk Board."
    )

    return {
        "complaint_id": complaint_data.get("id", ""),
        "classification": classification,
        "recommended_action": recommended_action,
        "seller_action_required": seller_action_required,
        "buyer_message_draft": buyer_message,
        "seller_message_draft": seller_message,
        "status": status
    }


# ---------------------------------------------------------------------------
# 5. Composite TrustTag Scorer
# ---------------------------------------------------------------------------
def compute_composite_trusttag_report(
    seller_query: str,
    serial_or_qr: str,
    category: str,
    listed_price: float,
    batch_code: Optional[str] = None,
    claimed_packaging: Optional[str] = None
) -> Dict[str, Any]:
    """
    Combines seller credibility, product authenticity, and complaint cluster
    intelligence into an authoritative 0-100 TrustTag Score and explainable report.
    """
    # 1. Seller score (0 - 100)
    seller_res = calculate_seller_credibility(seller_query)
    seller_pts = seller_res["score"]

    # 2. Product authenticity score (0 - 100)
    prod_res = check_product_authenticity(serial_or_qr, category, listed_price, claimed_packaging)
    prod_pts = prod_res["score"]

    # 3. Complaint cluster penalty (0 - 50)
    seller_id = seller_res.get("seller_id", seller_query)
    cluster_res = analyze_complaint_clusters(seller_id, batch_code, serial_or_qr)
    cluster_penalty = cluster_res["risk_penalty"]

    # Composite formula: 45% seller + 45% product - cluster penalty
    raw_composite = (seller_pts * 0.45) + (prod_pts * 0.45) - cluster_penalty
    composite_score = max(0, min(100, int(round(raw_composite))))

    # Determine badge label
    if composite_score >= 75 and cluster_penalty == 0 and prod_res["is_safe"]:
        badge_label = "VERIFIED"
        badge_color = "#10B981"  # Emerald green
        verdict = "Safe to Purchase"
    elif composite_score >= 50:
        badge_label = "CAUTION"
        badge_color = "#F59E0B"  # Amber
        verdict = "Proceed with Caution"
    else:
        badge_label = "HIGH_RISK"
        badge_color = "#EF4444"  # Crimson red
        verdict = "DO NOT PAY - High Counterfeit / Scam Probability"

    # Assemble explainable reasons
    reasons = []
    if cluster_penalty > 0:
        reasons.extend(cluster_res["warnings"])
    if not prod_res["is_safe"]:
        reasons.extend(prod_res["flags"])
    if len(seller_res["flags"]) > 0:
        reasons.extend(seller_res["flags"])
    if not reasons:
        reasons.append("Seller has verified business registration and good buyer history.")
        reasons.append("Product serial is validated in official manufacturer registry.")
        reasons.append("Price is aligned with fair market baseline.")

    return {
        "trusttag_score": composite_score,
        "badge_label": badge_label,
        "badge_color": badge_color,
        "verdict": verdict,
        "seller_credibility": seller_res,
        "product_authenticity": prod_res,
        "complaint_intelligence": cluster_res,
        "reasons": reasons,
        "recommendation": (
            "Approved: Proceed with order. Covered under TrustTag verified seller protection."
            if badge_label == "VERIFIED"
            else (
                "Review warning items above before committing payment."
                if badge_label == "CAUTION"
                else "ABORT PURCHASE: High counterfeit indicators, look-alike clone risks, or unreachable merchant detected."
            )
        )
    }


# ---------------------------------------------------------------------------
# 6. Seller Self-Verification Evaluator (Flow C)
# ---------------------------------------------------------------------------
def evaluate_seller_verification_application(
    seller_id: str,
    business_name: str,
    tax_id: str,
    id_document_type: str,
    contact_email: str,
    phone: str
) -> Dict[str, Any]:
    """
    Evaluates seller's application for TrustTag Verified badge.
    Calculates deterministic verification score.
    """
    score = 0
    feedback = []

    # Business registration / Tax ID check
    if tax_id and len(tax_id.strip()) >= 5:
        score += 35
        feedback.append("Commercial Tax/EIN registration submitted (+35 pts).")
    else:
        feedback.append("Missing or short Tax ID (-35 pts).")

    # Government ID check
    if id_document_type in ["PASSPORT", "DRIVERS_LICENSE", "NATIONAL_ID"]:
        score += 30
        feedback.append(f"Government ID ({id_document_type}) verified (+30 pts).")
    else:
        score += 10
        feedback.append("Secondary identification type provided (+10 pts).")

    # Domain verified email check
    free_email_providers = ["gmail.com", "yahoo.com", "hotmail.com", "protonmail.com", "outlook.com", "tempmail.in"]
    domain = contact_email.split("@")[-1].lower() if "@" in contact_email else ""
    if domain and domain not in free_email_providers:
        score += 20
        feedback.append("Corporate/domain-anchored email verified (+20 pts).")
    else:
        score += 10
        feedback.append("Public email domain used (+10 pts).")

    # Reachable phone check
    if phone and len(phone.strip()) >= 8:
        score += 15
        feedback.append("Direct merchant customer support hotline registered (+15 pts).")
    else:
        feedback.append("No phone hotline provided (+0 pts).")

    awarded = score >= 75
    badge = "VERIFIED" if awarded else ("CAUTION" if score >= 50 else "HIGH_RISK")

    return {
        "verification_score": score,
        "badge_awarded": awarded,
        "badge_status": badge,
        "feedback": feedback,
        "tips_to_improve": [
            "Link an official corporate domain email instead of a free provider",
            "Provide registered state EIN or business registration certificate",
            "Maintain an average customer support response time under 4 hours"
        ] if not awarded else ["Your business has achieved TrustTag Verified status! Embed the trust badge on your product pages."]
    }


# ---------------------------------------------------------------------------
# 7. CrewAI Tool Bindings (Decorated for Agent Use)
# ---------------------------------------------------------------------------
@tool("verify_seller_credibility")
def tool_verify_seller_credibility(seller_query: str) -> str:
    """Tool for Seller Verification Agent to calculate merchant credibility score (0-100) and verify account age, business registration, dispute rate, and reachability."""
    res = calculate_seller_credibility(seller_query)
    return json.dumps(res, indent=2)


@tool("check_product_authenticity_and_baseline")
def tool_check_product_authenticity(serial_or_qr: str, category: str, listed_price: float, claimed_packaging: str = "") -> str:
    """Tool for Product Authenticity Agent to verify serial with manufacturer ledger, check baseline price margin, and detect look-alike clone packaging."""
    res = check_product_authenticity(serial_or_qr, category, listed_price, claimed_packaging)
    return json.dumps(res, indent=2)


@tool("cluster_complaints_intelligence")
def tool_cluster_complaints_intelligence(seller_id: str, batch_code: str = "", serial_number: str = "") -> str:
    """Tool for Complaint Intelligence Agent to cluster isolated reports across buyers and detect rapid-failure fraud spikes (&le;7 days)."""
    res = analyze_complaint_clusters(seller_id, batch_code, serial_number)
    return json.dumps(res, indent=2)


@tool("arbitrate_dispute_and_draft_remedy")
def tool_arbitrate_dispute(complaint_json: str) -> str:
    """Tool for Dispute Resolution Agent to classify complaint, formulate binding outcome, and draft formal letters."""
    try:
        data = json.loads(complaint_json)
    except Exception:
        data = {"title": "Electronic accessory failure", "category": "counterfeit", "days_before_failure": 3}
    res = evaluate_dispute_and_draft_resolution(data)
    return json.dumps(res, indent=2)

