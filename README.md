# 🛡️ TrustTag — Anti-Counterfeit Trust Layer for Online Electronics

> **Scenario 19 Seminar Demo MVP**  
> Built with **CrewAI Multi-Agent Architecture**, **Deterministic Audit Tools**, **SQLite Persistence**, and an **Offline Stage-Proof Demo Mode**.

---

## 📌 Problem Analysis & Solution Overview

### The Official Scenario (Scenario 19: The Counterfeit Product Problem)
> *"A buyer pays a tempting price to an unfamiliar seller for an electronic accessory in look-alike packaging. It fails within days and the seller becomes unreachable. Other buyers report the same, and it's hard to tell which sellers are trustworthy, what's genuine, or how to resolve complaints. Honest businesses lose trust too."*

### Our Problem Statement
Online buyers of low-cost electronic accessories cannot verify whether a seller is legitimate or a product is genuine before paying. After a failure, they have no reliable way to reach the seller or resolve the complaint. Because each victim's complaint sits in isolation, scam patterns stay invisible, counterfeiters keep operating under burner accounts, and honest sellers lose customers' trust.

### 5 Root Causes & How TrustTag Solves Them
1. **Information Asymmetry:** Buyers cannot evaluate unfamiliar sellers before paying.  
   → **Solution (Flow A):** Pre-purchase multi-agent audit scoring seller history, account age, and reachability.
2. **No Authenticity Check:** Convincing look-alike packaging fools buyers.  
   → **Solution (Flow A):** Cross-checks serial/QR against authorized manufacturer registries and flags *tempting price lures* (e.g. 65W charger sold at $7.99 vs $34.99 baseline).
3. **Isolated Complaints:** Individual buyer reports are disconnected.  
   → **Solution (Flow D & Agent 3):** Complaint Intelligence Agent clusters reports across sellers, batches, and rapid failure windows (&le; 7 days).
4. **No Accountability:** Sellers ghost buyers with unreachable emails.  
   → **Solution (Flow B & Agent 4):** Dispute Arbitrator Agent classifies root cause and drafts binding refund/escalation notices.
5. **Honest Sellers Cannot Prove Authenticity:** Honest merchants suffer from collateral skepticism.  
   → **Solution (Flow C):** Structured merchant verification awards an embeddable *TrustTag Verified Badge*.

---

## 🤖 CrewAI Multi-Agent Architecture

TrustTag enforces a strict **deterministic calculation rule**: all mathematical scores, price baselines, and cluster thresholds are calculated in pure Python inside `tools.py`. The LLMs/Agents handle classification, contextual reasoning, and drafting communications.

| Agent | Role | Responsibility |
|---|---|---|
| **1. Seller Verification Agent** | Senior Merchant Credibility Auditor | Computes 0-100 credibility from account age, registered tax ID, order history, and contact reachability. |
| **2. Product Authenticity Agent** | Hardware Authenticity Specialist | Validates serial against official manufacturer registry, detects "tempting price" clone lures, and inspects packaging signatures. |
| **3. Complaint Intelligence Agent** | Pattern Clustering Detective | Groups complaints by batch/seller; triggers critical alert if &ge;3 complaints report failure within &le;7 days. |
| **4. Dispute Resolution Agent** | Fair-Trade Dispute Arbitrator | Classifies complaints (`COUNTERFEIT_SCAM`, `EARLY_DEFECT`, `NON_DELIVERY`), specifies remedies, and drafts buyer/merchant letters. |
| **5. Trust Score Agent (Synthesizer)** | Chief Trust Architect | Synthesizes multi-agent signals into a definitive 0-100 TrustTag Score and plain-English explanation. |

---

## 🚀 Quickstart & Installation (Windows 11, macOS, Linux)

### Prerequisites
- Python 3.10 or higher
- Git (optional)

### Step 1: Clone or Open Directory
```bash
cd trusttag
```

### Step 2: Create and Activate Virtual Environment
**On Windows 11 (Command Prompt / PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

*(Optional)* To test with live OpenAI LLMs, copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Otherwise, keep the default **⚡ Offline Demo Mode** toggled ON in the sidebar for guaranteed 0-latency seminar execution.

---

## ⏱️ 2-Minute Seminar Live Demo Script

Use this exact script for an impactful seminar presentation:

### Phase 1: The Honest Seller Demo (0:00 - 0:40)
1. In the sidebar, select **Preset 1: Honest Merchant (Apex Electro + Anker 65W)**.
2. Click **🚀 Run Multi-Agent Trust Audit**.
3. **Show the Audience:**
   - Score: **90/100 (VERIFIED - Green)**.
   - Point out: Registered business number on file, 38 months account age, valid manufacturer serial, price ($54.99) matches fair market baseline ($34.99 - $55.00).

### Phase 2: The Look-Alike Counterfeit Trap (0:40 - 1:20)
1. In the sidebar, select **Preset 2: Fraudulent Clone Scammer (MegaDiscount 65W Clone)**.
2. Click **🚀 Run Multi-Agent Trust Audit**.
3. **Show the Audience the Shocking Contrast:**
   - Score: **0/100 (HIGH RISK - Crimson Red)** with "DO NOT PAY" verdict!
   - Show the 3 Red Flags caught:
     - **Tempting Price Alert**: Listed at $7.99 (85% below market, below manufacturing cost).
     - **Serial Blacklist**: Clone serial not in manufacturer registry.
     - **Active Fraud Cluster**: 9 previous buyers reported sudden failure in &le; 4 days, and seller ghosted all of them.

### Phase 3: Buyer Complaint & Closing the Loop (1:20 - 2:00)
1. Switch to **Flow B: Report a Problem**.
2. Select seller `MegaDiscount Deals Hub`, price `$8.99`, failure on `Day 3`.
3. Click **⚖️ Submit Dispute & Trigger Arbitrator Agent**.
4. Show the instant **Case ID**, the automated `COUNTERFEIT_SCAM_ESCALATION` verdict, and the drafted demand letter.
5. Navigate to **Flow D: Public Risk Board** to show how this new report instantly updates the platform fraud radar, protecting the next buyer.

---

## 📁 Repository File Tree
```
├── app.py              # Streamlit 4-flow interactive user interface
├── agents.py           # CrewAI 5-agent definitions, roles, and runners
├── tasks.py            # CrewAI task specifications and expected outputs
├── tools.py            # Pure deterministic scoring math, price baselines, and clustering logic
├── database.py         # SQLite connection, schema migrations, and CRUD helpers
├── seed_data.json      # 10 sellers, 15 products with manufacturer ledger, 25 complaints
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md           # Documentation, architecture, and seminar demo guide
```

---

## 💡 Known Limitations & Future Roadmap
- **Decentralized Cryptographic RFID:** Future versions could verify physical NFC tags physically embedded in packaging rather than printed serials.
- **Automated Platform Delisting API:** Direct webhook integration with marketplaces (Amazon, eBay, Shopify) to automatically pause listings when a fraud cluster penalty exceeds 40 points.
- **Smart Contract Escrow:** Hold payment in smart escrow for 7 days until buyer verifies functionality.
