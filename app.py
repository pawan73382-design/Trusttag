"""
TrustTag - Seminar-Ready Multi-Agent Anti-Counterfeit Platform
Streamlit Application (app.py)

User Flows Implemented:
Flow A: Buyer "Check Before You Pay" (Pre-purchase trust verification)
Flow B: Buyer "Report a Problem" (Complaint filing, dispute AI classification & remedies)
Flow C: Seller "Get Verified" (Merchant credentialing & TrustTag Verified badge)
Flow D: Public "Risk Board" (Fraud radar & complaint-cluster alerts)
"""

import os
import json
import streamlit as st
import database
import tools
import agents

# Ensure database is initialized
database.init_db()

# Page configuration
st.set_page_config(
    page_title="TrustTag | Anti-Counterfeit Trust Layer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished seminar presentation
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #475569;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-card {
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    }
    .badge-verified {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    }
    .badge-caution {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
    }
    .badge-highrisk {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
    }
    .agent-step {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1rem;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }
    .risk-alert {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar Navigation & Seminar Demo Controls
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🛡️ **TrustTag Control Center**")
st.sidebar.caption("Anti-Counterfeit Multi-Agent Trust Architecture")

# Seminar Quick Demo Presets
st.sidebar.markdown("---")
st.sidebar.markdown("🎯 **Seminar Quick Presets (1-Click Demo)**")
demo_preset = st.sidebar.selectbox(
    "Load Scenario:",
    [
        "Custom Input",
        "1. Honest Merchant (Apex Electro + Anker 65W)",
        "2. Fraudulent Clone Scammer (MegaDiscount 65W Clone)",
        "3. Look-Alike Fake Earbuds (SuperSonic Tech)",
        "4. Unverified Neutral Seller (QuickBargain Cable)"
    ]
)

offline_mode = st.sidebar.toggle("⚡ Offline Demo Mode", value=True, help="Uses deterministic local tools and pre-computed agent reasoning. Safe for live stage seminars with no API key or WiFi drop risk.")

st.sidebar.markdown("---")
nav_choice = st.sidebar.radio(
    "Select Platform Flow:",
    [
        "Flow A: Check Before You Pay",
        "Flow B: Report a Problem",
        "Flow C: Seller 'Get Verified'",
        "Flow D: Public Risk Board",
        "CrewAI Architecture & Logs"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Seminar Pitch**: Solving Scenario 19 by turning isolated complaints into collective fraud intelligence before buyers pay."
)


# ===========================================================================
# FLOW A: Buyer "Check Before You Pay"
# ===========================================================================
if nav_choice == "Flow A: Check Before You Pay":
    st.markdown('<div class="main-title">🔍 Buyer Pre-Purchase Trust Check</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Verify seller credibility, cross-reference serial numbers with the manufacturer registry, and detect tempting counterfeit price lures.</div>', unsafe_allow_html=True)

    # Preset autofills
    default_seller = "Apex Electro Direct"
    default_serial = "ANK-735-882190"
    default_cat = "charger"
    default_price = 54.99
    default_batch = "BATCH-ANK-2024-Q1"
    default_pkg = "Original retail box with hologram seal"

    if demo_preset == "2. Fraudulent Clone Scammer (MegaDiscount 65W Clone)":
        default_seller = "MegaDiscount Deals Hub"
        default_serial = "CLONE-BATCH-BL2024-X9"
        default_cat = "charger"
        default_price = 7.99
        default_batch = "BL-2024-X9"
        default_pkg = "Looks like Anker 735 blue/white retail box"
    elif demo_preset == "3. Look-Alike Fake Earbuds (SuperSonic Tech)":
        default_seller = "SuperSonic Tech Outlet"
        default_serial = "SND-LIB4-CLONE-01"
        default_cat = "earbuds"
        default_price = 11.99
        default_batch = "BATCH-CLONE-EAR-01"
        default_pkg = "Lookalike packaging with Soundcore typography"
    elif demo_preset == "4. Unverified Neutral Seller (QuickBargain Cable)":
        default_seller = "QuickBargain Gadgets"
        default_serial = "FAKE-CBL-USBC-01"
        default_cat = "cable"
        default_price = 3.49
        default_batch = "SW-CHEAP-BATCH"
        default_pkg = "Unlabeled polybag with barcode sticker"

    col_input1, col_input2 = st.columns([1, 1])

    with col_input1:
        st.subheader("1. Merchant & Product Input")
        seller_input = st.text_input("Seller ID or Name", value=default_seller, help="Merchant ID (e.g. SEL-HONEST-01) or business trading name")
        serial_input = st.text_input("Product Serial Number / QR Code", value=default_serial, help="Barcode/Serial printed on packaging or listing")
        batch_input = st.text_input("Batch / Lot Code (Optional)", value=default_batch, help="Batch code from listing or box flap (e.g. BL-2024-X9)")

    with col_input2:
        st.subheader("2. Pricing & Category")
        category_input = st.selectbox(
            "Accessory Category",
            ["charger", "earbuds", "cable", "power_bank", "smartwatch_strap"],
            index=["charger", "earbuds", "cable", "power_bank", "smartwatch_strap"].index(default_cat) if default_cat in ["charger", "earbuds", "cable", "power_bank", "smartwatch_strap"] else 0
        )
        price_input = st.number_input("Listed Price ($ USD)", value=float(default_price), min_value=0.50, max_value=500.0, step=1.0)
        pkg_input = st.text_input("Claimed Packaging Description", value=default_pkg, help="Photo appearance, sealing method, claims")

    st.write("")
    run_check = st.button("🚀 Run Multi-Agent Trust Audit", type="primary", use_container_width=True)

    if run_check:
        with st.spinner("Executing CrewAI Agents: Seller Verification, Product Authenticity & Complaint Intelligence..."):
            report = agents.run_trust_evaluation(
                seller_query=seller_input,
                serial_or_qr=serial_input,
                category=category_input,
                listed_price=price_input,
                batch_code=batch_input,
                claimed_packaging=pkg_input,
                force_offline=offline_mode
            )

        # Result Presentation
        st.markdown("---")
        score = report["trusttag_score"]
        badge = report["badge_label"]
        verdict = report["verdict"]

        card_class = "badge-verified" if badge == "VERIFIED" else ("badge-caution" if badge == "CAUTION" else "badge-highrisk")
        badge_symbol = "✅" if badge == "VERIFIED" else ("⚠️" if badge == "CAUTION" else "🛑")

        st.markdown(f"""
        <div class="badge-card {card_class}">
            <h1 style="margin:0; font-size: 2.8rem; font-weight:900;">{badge_symbol} {score}/100 — {badge}</h1>
            <h3 style="margin-top:0.3rem; opacity:0.95;">{verdict}</h3>
            <p style="margin-top:0.5rem; font-size:1.05rem; font-weight:500;">{report['recommendation']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Metric Columns
        m1, m2, m3, m4 = st.columns(4)
        seller_info = report["seller_credibility"]
        prod_info = report["product_authenticity"]
        cluster_info = report["complaint_intelligence"]

        m1.metric("Seller Credibility", f"{seller_info['score']}/100", f"{seller_info.get('account_age_months', 0)} mos age")
        m2.metric("Authenticity Score", f"{prod_info['score']}/100", prod_info["authenticity_label"])
        m3.metric("Market Baseline Gap", f"${price_input:.2f}", f"Avg ${prod_info['market_comparison']['baseline_avg']:.2f}")
        m4.metric("Cluster Penalty", f"-{cluster_info['risk_penalty']} pts", f"{cluster_info['total_batch_complaints']} batch reports")

        # Plain Language Reasons (Crucial seminar requirement)
        st.subheader("📋 Explainable Audit Breakdown (Why this score?)")
        for reason in report["reasons"]:
            if "CRITICAL" in reason or "SCAM" in reason or "TEMPTING PRICE" in reason or "DO NOT PAY" in reason:
                st.error(f"🚨 {reason}")
            elif "warning" in reason.lower() or "caution" in reason.lower() or "below" in reason.lower():
                st.warning(f"⚠️ {reason}")
            else:
                st.success(f"✓ {reason}")

        # Multi-Agent Workflow Details
        with st.expander("🤖 Inspect Multi-Agent Crew Execution Log", expanded=True):
            for log in report["agent_logs"]:
                st.markdown(f"""
                <div class="agent-step">
                    <b>{log['agent']}</b> <span style="color:#64748b; font-size:0.85rem;">[{log['status']}]</span><br>
                    <span style="color:#0f172a; font-size:0.95rem;"><b>Action:</b> {log['action']}</span><br>
                    <span style="color:#1e293b;"><b>Result:</b> {log['result']}</span><br>
                    <span style="color:#475569; font-style: italic;"><b>Reasoning:</b> {log['reasoning']}</span>
                </div>
                """, unsafe_allow_html=True)


# ===========================================================================
# FLOW B: Buyer "Report a Problem"
# ===========================================================================
elif nav_choice == "Flow B: Report a Problem":
    st.markdown('<div class="main-title">📢 Report a Problem & Resolve Dispute</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Submit counterfeit or defective accessory complaints. Connects your report with other victims to reveal scam patterns and automatically drafts binding resolutions.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("Complaint Particulars")
        sellers_list = database.get_all_sellers()
        seller_options = {s["id"]: f"{s['name']} ({s['id']})" for s in sellers_list}

        sel_id = st.selectbox(
            "Select Merchant",
            options=list(seller_options.keys()),
            format_func=lambda x: seller_options.get(x, x),
            index=list(seller_options.keys()).index("SEL-FRAUD-01") if "SEL-FRAUD-01" in seller_options else 0
        )
        buyer_name = st.text_input("Your Full Name", value="Alex Morgan")
        buyer_email = st.text_input("Your Email Address", value="alex.morgan@seminar-demo.org")
        prod_serial = st.text_input("Product Serial Number (if known)", value="CLONE-BATCH-BL2024-X9")
        batch_code = st.text_input("Batch / Lot Number", value="BL-2024-X9")

    with c2:
        st.subheader("Incident Evidence")
        category_choice = st.selectbox(
            "Problem Category",
            ["counterfeit", "defective", "non_delivery", "unreachable_seller"]
        )
        purchase_price = st.number_input("Amount Paid ($ USD)", value=8.99, min_value=1.0, max_value=1000.0)
        days_to_fail = st.slider("Days Before Product Failed", min_value=1, max_value=90, value=3, help="How many days after delivery did it stop working or smoke?")
        complaint_title = st.text_input("Summary Title", value="Charger started smoking on Day 3. Seller email bounces.")
        complaint_desc = st.text_area(
            "Detailed Description & Packaging Clues",
            value="Look-alike blue box imitating Anker GaNPrime. Stopped charging and smelled like burning plastic after 3 days. Merchant phone is dead and support email rejected message.",
            height=120
        )

    submit_complaint = st.button("⚖️ Submit Dispute & Trigger Arbitrator Agent", type="primary", use_container_width=True)

    if submit_complaint:
        complaint_payload = {
            "seller_id": sel_id,
            "product_serial": prod_serial,
            "batch_code": batch_code,
            "buyer_name": buyer_name,
            "buyer_email": buyer_email,
            "purchase_price": purchase_price,
            "days_before_failure": days_to_fail,
            "category": category_choice,
            "title": complaint_title,
            "description": complaint_desc,
            "seller_responded": False,
            "status": "ESCALATED"
        }

        with st.spinner("Complaint Intelligence Agent indexing graph & Dispute Arbitrator formulating outcome..."):
            dispute_outcome = agents.run_dispute_resolution_workflow(complaint_payload, force_offline=offline_mode)

        st.success(f"✓ Complaint successfully saved! Case ID: **{dispute_outcome['complaint_id']}**")

        st.subheader("🏛️ Dispute Resolution Agent Recommendation")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.info(f"**Classification:** {dispute_outcome['classification']}")
            st.warning(f"**Recommended Remedy:** {dispute_outcome['recommended_action']}")
            st.error(f"**Merchant Action Required:** {dispute_outcome['seller_action_required']}")

        with res_col2:
            st.markdown("##### ✉️ Drafted Notice to Buyer")
            st.code(dispute_outcome["buyer_message_draft"], language="text")

        st.markdown("##### ⚠️ Formal Legal Notice Drafted for Merchant")
        st.code(dispute_outcome["seller_message_draft"], language="text")

        # Show that this immediately feeds future trust scores
        st.info("🔄 **Loop Closed**: This complaint has been written to the SQLite database. Any future buyers scanning batch BL-2024-X9 will immediately see this failure cluster in Flow A!")


# ===========================================================================
# FLOW C: Seller "Get Verified"
# ===========================================================================
elif nav_choice == "Flow C: Seller 'Get Verified'":
    st.markdown('<div class="main-title">🏅 Seller Verification Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Honest merchants can prove their legitimacy, submit business credentials, earn a TrustTag Verified Badge, and receive transparent guidance to improve their score.</div>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([1, 1])

    with col_s1:
        st.subheader("Merchant Credentials Submission")
        s_id = st.text_input("Existing Seller ID (or leave blank for new)", value="SEL-NEW-01")
        b_name = st.text_input("Registered Business Name", value="Aurora Mobile Accessories LLC")
        tax_id = st.text_input("Business Tax ID / State Registration / EIN", value="EIN-84-2918204", help="Official commercial registration code")
        doc_type = st.selectbox(
            "Government Photo ID Document",
            ["PASSPORT", "DRIVERS_LICENSE", "NATIONAL_ID", "UTILITY_BILL"]
        )
        c_email = st.text_input("Official Domain Contact Email", value="compliance@auroramobile.com", help="Domain-backed emails score higher than disposable/free mailboxes")
        c_phone = st.text_input("Customer Support Telephone", value="+1-415-555-0182")

        submit_verif = st.button("🛡️ Audit Credentials & Issue Trust Badge", type="primary")

    with col_s2:
        st.subheader("Verification Rubric & Criteria")
        st.markdown("""
        - **Business Registration (+35 pts)**: Verified EIN/commercial ledger match.
        - **Government Identity (+30 pts)**: Authenticated passport or state driver's license.
        - **Domain Anchored Support (+20 pts)**: Official business domain (e.g. `@auroramobile.com`).
        - **Customer Hotline (+15 pts)**: Active monitored phone line.
        - **Passing Score**: **>= 75 pts** unlocks the **TrustTag Verified Digital Badge**.
        """)

        if submit_verif:
            eval_res = tools.evaluate_seller_verification_application(
                seller_id=s_id,
                business_name=b_name,
                tax_id=tax_id,
                id_document_type=doc_type,
                contact_email=c_email,
                phone=c_phone
            )

            # Save in database
            save_payload = {
                "seller_id": s_id,
                "business_name": b_name,
                "tax_id": tax_id,
                "id_document_type": doc_type,
                "contact_email": c_email,
                "phone": c_phone,
                "verification_score": eval_res["verification_score"],
                "remarks": "; ".join(eval_res["feedback"])
            }
            db_res = database.save_seller_verification(save_payload)

            st.write("---")
            score = eval_res["verification_score"]
            awarded = eval_res["badge_awarded"]

            if awarded:
                st.success(f"🎉 **CONGRATULATIONS! Verification Score: {score}/100**")
                st.markdown(f"""
                <div class="badge-card badge-verified">
                    <h2 style="margin:0;">🛡️ TrustTag VERIFIED MERCHANT</h2>
                    <p style="margin:0.4rem 0 0 0;">Licensed Entity: <b>{b_name}</b></p>
                    <p style="margin:0.2rem 0 0 0; font-size:0.9rem; opacity:0.9;">Digital Trust Seal ID: {db_res['verification_id']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("Embeddable TrustTag Badge Code for Checkout:")
                st.code(f"""<!-- TrustTag Verified Merchant Widget -->
<div class="trusttag-badge" data-seller="{s_id}" data-status="VERIFIED">
  <span class="trusttag-icon">🛡️</span> Verified by TrustTag Multi-Agent Protocol
</div>
<script src="https://trusttag.dev/shield.js" async></script>""", language="html")
            else:
                st.warning(f"Verification Score: {score}/100 — Status: {eval_res['badge_status']}")
                st.write("**Next Steps to Achieve Verified Badge:**")
                for tip in eval_res["tips_to_improve"]:
                    st.write(f"- {tip}")


# ===========================================================================
# FLOW D: Public "Risk Board"
# ===========================================================================
elif nav_choice == "Flow D: Public Risk Board":
    st.markdown('<div class="main-title">🚨 Public Risk Board & Fraud Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-time scam pattern detector aggregating isolated complaints. Exposes active counterfeit batches, rapid failure clusters, and ghosting merchants.</div>', unsafe_allow_html=True)

    clusters = database.find_complaint_clusters(min_reports=2, max_days_threshold=7)

    st.subheader(f"⚡ Active High-Risk Fraud Clusters ({len(clusters)} Detected)")

    for c in clusters:
        st.markdown(f"""
        <div class="risk-alert">
            <h4 style="margin:0; color:#b91c1c;">⚠️ CRITICAL CLUSTER: Batch Code '{c['batch_code']}'</h4>
            <p style="margin:0.4rem 0; color:#334155;">
                <b>Seller:</b> {c['seller_name']} (ID: {c['seller_id']}) &nbsp;|&nbsp; 
                <b>Total Complaints:</b> {c['report_count']} &nbsp;|&nbsp; 
                <b>Rapid Failures (&le;7 Days):</b> <span style="color:#dc2626; font-weight:bold;">{c['rapid_failures']}</span> &nbsp;|&nbsp;
                <b>Ghosted Buyers:</b> {c['ghosted_buyers']}
            </p>
            <p style="margin:0; color:#64748b; font-size:0.9rem;">
                <b>Pattern Analysis:</b> Look-alike packaging sold at tempting discount. 100% of reported units failed within an average of {c['avg_days_to_fail']:.1f} days. Seller support email is disconnected.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("📜 Live Feed of Recent Platform Complaints")
    all_complaints = database.get_all_complaints(limit=15)
    
    # Format table
    table_data = []
    for comp in all_complaints:
        table_data.append({
            "Case ID": comp["id"],
            "Seller": comp.get("seller_name") or comp["seller_id"],
            "Batch": comp.get("batch_code") or "N/A",
            "Days to Fail": f"{comp.get('days_before_failure')} days",
            "Category": comp["category"].upper(),
            "Title": comp["title"][:50] + ("..." if len(comp["title"]) > 50 else ""),
            "Status": comp["status"]
        })

    st.dataframe(table_data, use_container_width=True)


# ===========================================================================
# VIEW 5: CrewAI Architecture & Logs
# ===========================================================================
elif nav_choice == "CrewAI Architecture & Logs":
    st.markdown('<div class="main-title">🧠 CrewAI Multi-Agent Architecture</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Inspection of agent roles, goal specifications, tool bindings, and deterministic guardrails.</div>', unsafe_allow_html=True)

    st.markdown("""
    ### 5-Agent Collaborative Pipeline
    ```
    [ Buyer Request / Listing Data ]
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    [Agent 1: Seller]   [Agent 2: Product] 
    Credibility Audit   Registry & Tempting Price
        │                   │
        └─────────┬─────────┘
                  ▼
        [Agent 3: Complaint Intelligence]
        Cluster Detection & Cross-Victim Graph
                  │
                  ▼
        [Agent 5: Trust Score Synthesizer]
        0-100 Score + Explainable Plain Language
                  │
                  ▼
        [ Flow A: Pre-Purchase Trust Report ]
    ```
    ---
    ### Agent Specifications
    """)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("""
        **1. Seller Verification Agent**
        - **Role**: Senior Merchant Credibility Auditor
        - **Goal**: Audit account age, commercial registration, dispute rates, and reachability.
        - **Deterministic Rule**: Calculates score 0-100 based on verified tax ID (+35), age (+25), low complaint ratio (+25), and responsive contact (+15).

        **2. Product Authenticity Agent**
        - **Role**: Hardware Authenticity & Anti-Counterfeit Specialist
        - **Goal**: Cross-check serial numbers with manufacturer registry and identify clone lures.
        - **Deterministic Rule**: Flags any listing priced > 50% below manufacturing baseline as high counterfeit probability.
        """)

    with col_a2:
        st.markdown("""
        **3. Complaint Intelligence Agent**
        - **Role**: Complaint Intelligence & Pattern Clustering Detective
        - **Goal**: Unify isolated reports by seller, product, and batch code.
        - **Deterministic Rule**: If >= 3 complaints with failure <= 7 days, raises Critical Fraud Cluster with -45 pts penalty.

        **4. Dispute Resolution Agent**
        - **Role**: Fair-Trade Dispute Arbitrator & Mediation Counsel
        - **Goal**: Auto-classify failure root causes and draft enforceable remedies.
        """)
