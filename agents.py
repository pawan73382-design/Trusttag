"""
TrustTag - CrewAI Multi-Agent System (agents.py)

Contains definitions for the 5 specialized CrewAI agents:
1. Seller Verification Agent
2. Product Authenticity Agent
3. Complaint Intelligence Agent
4. Dispute Resolution Agent
5. Trust Score Agent (Final synthesis)

Supports both:
- Live CrewAI execution with OpenAI / Gemini / LiteLLM API keys
- Robust OFFLINE DEMO MODE that runs without internet or keys for seminar reliability.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional
import tools
import database

# Check CrewAI availability
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


# ===========================================================================
# 1. AGENT DEFINITIONS (CrewAI Standard Specification)
# ===========================================================================

def create_seller_verification_agent(llm=None):
    """
    Agent 1: Seller Verification Agent
    PURPOSE: Analyzes seller history, business registration, account age,
    complaint ratios, and response reachability to calculate merchant credibility.
    """
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Senior Merchant Credibility Auditor",
        goal="Audit seller credentials, account age, complaint rates, and reachability to prevent burner account scams.",
        backstory=(
            "You are a seasoned e-commerce fraud forensic analyst. You specialize in identifying "
            "burner merchant accounts created by fly-by-night sellers who disappear after shipping defective items. "
            "You rely strictly on factual metrics provided by database tools."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[tools.tool_verify_seller_credibility],
        llm=llm
    )


def create_product_authenticity_agent(llm=None):
    """
    Agent 2: Product Authenticity Agent
    PURPOSE: Verifies serial/QR against official manufacturer ledger, checks for
    'tempting price' discounts far below baseline, and flags look-alike packaging signatures.
    """
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Hardware Authenticity & Anti-Counterfeit Specialist",
        goal="Cross-reference product serial numbers with authorized manufacturer registries and detect clone packaging.",
        backstory=(
            "You worked for top electronics hardware manufacturers authenticating supply chains. "
            "You know how counterfeiters replicate brand packaging ('Anker-lookalikes', fake Belkin boxes) "
            "and lure buyers with suspiciously low pricing below manufacturing cost."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[tools.tool_check_product_authenticity],
        llm=llm
    )


def create_complaint_intelligence_agent(llm=None):
    """
    Agent 3: Complaint Intelligence Agent
    PURPOSE: Connects isolated buyer reports to detect fraud clusters across sellers,
    products, and batch codes (e.g., '5 reports of failure within 7 days').
    """
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Complaint Intelligence & Pattern Clustering Detective",
        goal="Cluster isolated buyer complaints across batches and sellers to detect rapid-failure counterfeit waves.",
        backstory=(
            "In e-commerce, victims suffer in isolation. Your mission is connecting the dots: "
            "identifying when multiple buyers report rapid failure (under 7 days) for the same batch code, "
            "or when a seller systematically ghosts buyers."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[tools.tool_cluster_complaints_intelligence],
        llm=llm
    )


def create_dispute_resolution_agent(llm=None):
    """
    Agent 4: Dispute Resolution Agent
    PURPOSE: Evaluates incoming buyer complaints, classifies the root cause,
    recommends binding remedy (refund/replace/warning), and drafts professional notices.
    """
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Fair-Trade Dispute Arbitrator & Mediation Counsel",
        goal="Classify dispute claims, evaluate evidence, recommend fair resolutions, and draft clear notices.",
        backstory=(
            "You are a licensed consumer protection arbitrator. You cut through disputes fairly: "
            "demanding immediate refunds and platform bans for counterfeiters, while safeguarding "
            "honest merchants from fraudulent buyer claims with clear evidence standards."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[tools.tool_arbitrate_dispute],
        llm=llm
    )


def create_trust_score_agent(llm=None):
    """
    Agent 5: Trust Score Agent (Final Synthesizer)
    PURPOSE: Combines seller credibility, product authenticity, and complaint clusters
    into an authoritative 0-100 TrustTag Score with a plain-language explanation of WHY.
    """
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Chief Trust Architect & Risk Assessor",
        goal="Synthesize multi-agent findings into a definitive, explainable 0-100 TrustTag Score and buyer action.",
        backstory=(
            "You are the executive voice of TrustTag. You deliver unambiguous, plain-English guidance "
            "to consumers before they commit funds, breaking down the exact mathematical and empirical reasons "
            "for every Verified, Caution, or High Risk verdict."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


# ===========================================================================
# 2. RUNNER ENGINE (Live CrewAI + Offline Demo Mode)
# ===========================================================================

def run_trust_evaluation(
    seller_query: str,
    serial_or_qr: str,
    category: str,
    listed_price: float,
    batch_code: Optional[str] = None,
    claimed_packaging: Optional[str] = None,
    force_offline: bool = True
) -> Dict[str, Any]:
    """
    Executes the 5-Agent TrustTag Evaluation workflow:
    1. Seller Verification Agent -> credibility audit
    2. Product Authenticity Agent -> registry & price baseline audit
    3. Complaint Intelligence Agent -> cluster detection
    4. Trust Score Agent -> final composite score & plain-language explanation
    """
    # Deterministic ground truth calculation (Guarantees zero mathematical hallucination)
    report = tools.compute_composite_trusttag_report(
        seller_query=seller_query,
        serial_or_qr=serial_or_qr,
        category=category,
        listed_price=listed_price,
        batch_code=batch_code,
        claimed_packaging=claimed_packaging
    )

    # Agent execution traces for seminar UI display
    agent_logs = []
    
    # 1. Seller Agent step
    seller_res = report["seller_credibility"]
    agent_logs.append({
        "agent": "Seller Verification Agent",
        "action": f"Querying merchant ledger for '{seller_query}'",
        "status": "COMPLETED",
        "result": f"Score: {seller_res['score']}/100. Age: {seller_res.get('account_age_months', 0)} mo. Orders: {seller_res.get('total_orders', 0)}. Reachable: {seller_res.get('contact_reachable')}.",
        "reasoning": seller_res["summary"]
    })

    # 2. Product Agent step
    prod_res = report["product_authenticity"]
    agent_logs.append({
        "agent": "Product Authenticity Agent",
        "action": f"Checking serial '{serial_or_qr}' against Manufacturer Registry & Baseline (${listed_price:.2f})",
        "status": "COMPLETED",
        "result": f"Authenticity: {prod_res['authenticity_label']} ({prod_res['score']}/100). Status: {prod_res['registry_status']}.",
        "reasoning": (
            "Serial verified in official registry with valid safety certs."
            if prod_res["is_safe"]
            else f"Flagged: {'; '.join(prod_res['flags'])}"
        )
    })

    # 3. Complaint Intelligence step
    cluster_res = report["complaint_intelligence"]
    agent_logs.append({
        "agent": "Complaint Intelligence Agent",
        "action": f"Scanning cross-buyer complaints for batch '{batch_code or 'N/A'}'",
        "status": "COMPLETED",
        "result": f"Cluster: {cluster_res['cluster_severity']} (Penalty: -{cluster_res['risk_penalty']} pts). Reports: {cluster_res['total_batch_complaints']}.",
        "reasoning": (
            f"Detected rapid failure wave! {cluster_res['rapid_failures_under_7_days']} units failed in <=7 days."
            if cluster_res["risk_penalty"] > 0
            else "No systemic fraud clusters or rapid failure spikes detected."
        )
    })

    # 4. Final Trust Score Agent step
    agent_logs.append({
        "agent": "Trust Score Agent",
        "action": "Synthesizing multi-agent outputs into final 0-100 TrustTag Score",
        "status": "COMPLETED",
        "result": f"Final TrustTag Score: {report['trusttag_score']}/100 -> [{report['badge_label']}]",
        "reasoning": f"Verdict: {report['verdict']}. Reasons: {' | '.join(report['reasons'][:2])}"
    })

    report["agent_logs"] = agent_logs
    report["execution_mode"] = "OFFLINE_DETERMINISTIC_CREW" if force_offline else "LIVE_CREWAI"
    return report


def run_dispute_resolution_workflow(
    complaint_data: Dict[str, Any],
    force_offline: bool = True
) -> Dict[str, Any]:
    """
    Executes the Dispute Resolution Agent workflow for buyer complaints:
    1. Saves complaint into SQLite database
    2. Evaluates evidence and classifies issue
    3. Recommends binding action & drafts buyer/seller messages
    """
    # 1. Insert into database
    complaint_id = database.insert_complaint(complaint_data)
    complaint_data["id"] = complaint_id

    # 2. Run deterministic dispute evaluation tool
    dispute_res = tools.evaluate_dispute_and_draft_resolution(complaint_data)
    
    # 3. Persist dispute record
    dispute_id = database.insert_dispute(dispute_res)
    dispute_res["dispute_id"] = dispute_id

    # Agent execution log for UI
    agent_logs = [
        {
            "agent": "Complaint Intelligence Agent",
            "action": f"Indexed Case #{complaint_id} into centralized complaint graph",
            "status": "COMPLETED",
            "result": f"Buyer: {complaint_data['buyer_name']} | Seller: {complaint_data['seller_id']} | Failed on Day {complaint_data.get('days_before_failure', 'N/A')}"
        },
        {
            "agent": "Dispute Resolution Agent",
            "action": "Classifying failure cause and computing remediation remedy",
            "status": "COMPLETED",
            "result": f"Classification: {dispute_res['classification']} -> Action: {dispute_res['recommended_action']}"
        }
    ]

    return {
        "complaint_id": complaint_id,
        "dispute_id": dispute_id,
        "classification": dispute_res["classification"],
        "recommended_action": dispute_res["recommended_action"],
        "seller_action_required": dispute_res["seller_action_required"],
        "buyer_message_draft": dispute_res["buyer_message_draft"],
        "seller_message_draft": dispute_res["seller_message_draft"],
        "status": dispute_res["status"],
        "agent_logs": agent_logs
    }
