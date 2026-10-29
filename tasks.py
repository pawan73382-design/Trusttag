"""
TrustTag - CrewAI Tasks Specification (tasks.py)

Defines the individual tasks for each of the 5 agents:
- AuditSellerTask: Seller Verification Agent
- VerifyProductTask: Product Authenticity Agent
- ClusterComplaintsTask: Complaint Intelligence Agent
- ResolveDisputeTask: Dispute Resolution Agent
- SynthesizeTrustScoreTask: Trust Score Agent
"""

from typing import Any, Dict, Optional

try:
    from crewai import Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


def create_seller_audit_task(agent, seller_query: str):
    """Task 1: Audit seller credibility and flag burner merchants."""
    if not CREWAI_AVAILABLE:
        return None
    return Task(
        description=(
            f"Query the merchant database for seller '{seller_query}'. "
            "Retrieve account age, business registration status, order history, "
            "complaint count, and customer service response reachability. "
            "Calculate seller credibility points (0-100) using the deterministic formula."
        ),
        expected_output=(
            "A structured dictionary containing seller credibility score (0-100), "
            "badge status (VERIFIED/CAUTION/HIGH_RISK), reachability status, and any risk flags."
        ),
        agent=agent
    )


def create_product_verify_task(agent, serial_or_qr: str, category: str, listed_price: float, claimed_packaging: str = ""):
    """Task 2: Check product against manufacturer registry and price baselines."""
    if not CREWAI_AVAILABLE:
        return None
    return Task(
        description=(
            f"Cross-check product serial '{serial_or_qr}' with the manufacturer registry. "
            f"Compare listed price (${listed_price:.2f}) against the {category} market baseline. "
            "Check for 'tempting price' clone lures (prices below manufacturing cost) "
            f"and analyze claimed packaging description ('{claimed_packaging}')."
        ),
        expected_output=(
            "A structured report with authenticity label (AUTHENTIC/SUSPICIOUS/COUNTERFEIT_ALERT), "
            "authenticity score (0-100), price margin anomaly flags, and packaging warnings."
        ),
        agent=agent
    )


def create_complaint_cluster_task(agent, seller_id: str, batch_code: str = ""):
    """Task 3: Cluster isolated complaints to expose systemic counterfeit waves."""
    if not CREWAI_AVAILABLE:
        return None
    return Task(
        description=(
            f"Analyze all historical buyer complaints for seller '{seller_id}' and batch code '{batch_code}'. "
            "Detect if a cluster exists (e.g., 3+ reports with failure within 7 days). "
            "Identify if seller is unreachable/ghosting buyers and calculate cluster risk penalty."
        ),
        expected_output=(
            "Cluster analysis summary with cluster severity, risk penalty (0-50 pts), "
            "number of rapid failures under 7 days, and ghosted buyer ratio."
        ),
        agent=agent
    )


def create_dispute_resolution_task(agent, complaint_data: Dict[str, Any]):
    """Task 4: Classify complaint, evaluate evidence, recommend remedy, and draft notices."""
    if not CREWAI_AVAILABLE:
        return None
    return Task(
        description=(
            f"Analyze new buyer complaint #{complaint_data.get('id', 'NEW')} against seller '{complaint_data.get('seller_id')}'. "
            f"Category: {complaint_data.get('category')}. Days to failure: {complaint_data.get('days_before_failure')}. "
            "Classify the failure into COUNTERFEIT_SCAM, EARLY_DEFECT, or NON_DELIVERY. "
            "Recommend binding remedy and draft formal communications to both buyer and merchant."
        ),
        expected_output=(
            "Structured dispute document with classification, recommended remedy, "
            "seller requirement, drafted buyer notification, and drafted merchant warning notice."
        ),
        agent=agent
    )


def create_trust_synthesis_task(agent, context_tasks: list):
    """Task 5: Synthesize all agent findings into final 0-100 TrustTag Score and plain-language explanation."""
    if not CREWAI_AVAILABLE:
        return None
    return Task(
        description=(
            "Synthesize outputs from Seller Verification, Product Authenticity, and Complaint Intelligence. "
            "Apply the deterministic formula: (Seller*0.45) + (Product*0.45) - Cluster Penalty. "
            "Assign final TrustTag badge (VERIFIED/CAUTION/HIGH_RISK) and generate a clear, "
            "actionable plain-language explanation for why this score was awarded."
        ),
        expected_output=(
            "Final TrustTag Report with 0-100 score, badge verdict, plain-English reasons, "
            "and recommended buyer action (Safe to Purchase / Caution / Do Not Pay)."
        ),
        agent=agent,
        context=context_tasks
    )
