"""
LedgerLens Streamlit Frontend — Premium Fintech Design
Clean light theme with strong contrast, crisp cards, and professional typography.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be FIRST Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LedgerLens — Invoice AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Clean Fintech Light Theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Background ── */
.stApp {
    background: #F8F9FC !important;
}
section[data-testid="stSidebar"] { display: none; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Top navbar strip ── */
.ll-navbar {
    background: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin: -1rem -1rem 2rem -1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.ll-logo {
    font-size: 1.5rem;
    font-weight: 800;
    color: #1E1E2E;
    letter-spacing: -0.03em;
}
.ll-logo span { color: #6366F1; }
.ll-tagline {
    font-size: 0.8rem;
    color: #6B7280;
    font-weight: 400;
    margin-left: 4px;
}
.ll-badge {
    background: #EEF2FF;
    color: #6366F1;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid #C7D2FE;
    margin-left: auto;
}

/* ── Section title ── */
.ll-section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
    letter-spacing: -0.01em;
}
.ll-section-sub {
    font-size: 0.85rem;
    color: #6B7280;
    margin-bottom: 20px;
}

/* ── Cards ── */
.ll-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── KPI metric cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 16px 0;
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    letter-spacing: -0.02em;
    line-height: 1;
}
.kpi-value.accent { color: #6366F1; }
.kpi-value.green  { color: #059669; }
.kpi-value.amber  { color: #D97706; }
.kpi-value.red    { color: #DC2626; }

/* ── Status pill ── */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
}
.pill-green  { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
.pill-amber  { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.pill-red    { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.pill-blue   { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.pill-purple { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }

/* ── Result banner ── */
.result-banner {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    font-size: 0.9rem;
}
.banner-success { background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; }
.banner-warning { background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }
.banner-error   { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }

/* ── Confidence bar ── */
.conf-bar-wrap { margin: 12px 0; }
.conf-bar-label { font-size: 0.78rem; font-weight: 600; color: #374151; margin-bottom: 6px; display: flex; justify-content: space-between; }
.conf-bar-track { background: #F3F4F6; border-radius: 6px; height: 8px; overflow: hidden; }
.conf-bar-fill  { height: 100%; border-radius: 6px; transition: width 0.4s ease; }
.conf-high-fill { background: linear-gradient(90deg, #10B981, #34D399); }
.conf-mid-fill  { background: linear-gradient(90deg, #F59E0B, #FCD34D); }
.conf-low-fill  { background: linear-gradient(90deg, #EF4444, #F87171); }

/* ── Table / DataFrame ── */
[data-testid="stDataFrame"] thead th {
    background: #F9FAFB !important;
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stDataFrame"] tbody td {
    color: #111827 !important;
    font-size: 0.85rem !important;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border-bottom: 2px solid #E5E7EB !important;
    border-radius: 0 !important;
    gap: 0 !important;
    padding: 0 !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
}
[aria-selected="true"] {
    color: #6366F1 !important;
    border-bottom: 2px solid #6366F1 !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #6366F1 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 10px 20px !important;
    box-shadow: 0 1px 3px rgba(99,102,241,0.3) !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: #4F46E5 !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Inputs & selects ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #111827 !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background: #FAFAFA !important;
    border: 2px dashed #D1D5DB !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #6366F1 !important;
    background: #EEF2FF !important;
}

/* ── Streamlit alerts (overridden) ── */
.stSuccess > div { background: #F0FDF4 !important; border-left: 4px solid #22C55E !important; color: #166534 !important; border-radius: 8px !important; }
.stError   > div { background: #FEF2F2 !important; border-left: 4px solid #EF4444 !important; color: #991B1B !important; border-radius: 8px !important; }
.stWarning > div { background: #FFFBEB !important; border-left: 4px solid #F59E0B !important; color: #92400E !important; border-radius: 8px !important; }
.stInfo    > div { background: #EFF6FF !important; border-left: 4px solid #3B82F6 !important; color: #1D4ED8 !important; border-radius: 8px !important; }

/* ── Expander ── */
[data-testid="stExpander"] > details {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* ── Metric override — make values WHITE area black ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
[data-testid="metric-container"] label {
    color: #6B7280 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid #E5E7EB !important; margin: 20px 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F3F4F6; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Navbar
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ll-navbar">
    <div class="ll-logo">🔍 Ledger<span>Lens</span></div>
    <div class="ll-tagline">Vision-Based Invoice Extraction</div>
    <div class="ll-badge">✦ AI-Powered</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def conf_color_class(c: float) -> str:
    if c >= 0.75: return "green"
    if c >= 0.5:  return "amber"
    return "red"

def conf_fill_class(c: float) -> str:
    if c >= 0.75: return "conf-high-fill"
    if c >= 0.5:  return "conf-mid-fill"
    return "conf-low-fill"

def confidence_bar(label: str, value: float):
    fill_cls = conf_fill_class(value)
    pct = int(value * 100)
    st.markdown(f"""
    <div class="conf-bar-wrap">
        <div class="conf-bar-label">
            <span>{label}</span>
            <span style="color:{'#059669' if pct>=75 else '#D97706' if pct>=50 else '#DC2626'};font-weight:700">{pct}%</span>
        </div>
        <div class="conf-bar-track">
            <div class="conf-bar-fill {fill_cls}" style="width:{pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def status_pill(status: str) -> str:
    mapping = {
        "auto_approved": ("pill-green",  "✓ Auto-approved"),
        "approved":      ("pill-green",  "✓ Approved"),
        "pending_review":("pill-amber",  "⏳ Pending Review"),
        "processed":     ("pill-blue",   "⚙ Processed"),
        "uploaded":      ("pill-purple", "↑ Uploaded"),
    }
    cls, label = mapping.get(status, ("pill-blue", status))
    return f'<span class="pill {cls}">{label}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["  Upload  ", "  Documents  ", "  Review Queue  ", "  Dashboard  "])


###############################################################################
# TAB 1 — UPLOAD
###############################################################################
with tab1:
    st.markdown('<div class="ll-section-title">Upload Invoice or Receipt</div>', unsafe_allow_html=True)
    st.markdown('<div class="ll-section-sub">Supports JPG and PNG · The AI extracts structured data with per-field confidence scores</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your invoice here, or click to browse",
        type=["jpg", "jpeg", "png"],
        label_visibility="visible",
    )

    if uploaded_file:
        col_img, col_result = st.columns([1, 1], gap="large")

        with col_img:
            st.image(uploaded_file, caption=f"📄 {uploaded_file.name}", use_container_width=True)

        with col_result:
            if st.button("⚡  Extract Invoice Data", use_container_width=True):
                with st.spinner("Running AI extraction pipeline…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/ingest",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                            timeout=120,
                        )

                        if response.status_code == 422:
                            err = response.json().get("detail", {})
                            if isinstance(err, dict) and err.get("error") == "moderation_blocked":
                                st.error(f"🚫 **Content blocked** — {err.get('blocked_reason', 'Policy violation')}")
                            else:
                                st.error(f"Validation error: {response.text}")

                        elif response.status_code == 200:
                            data = response.json()
                            summary  = data.get("extraction_summary", {})
                            flagged  = data.get("flagged_count", 0)
                            doc_status = data.get("status", "")
                            doc_id   = data["document_id"]
                            conf     = summary.get("overall_confidence") or 0

                            # ── Status banner ──
                            if doc_status == "auto_approved":
                                st.markdown(f"""
                                <div class="result-banner banner-success">
                                    ✅ Auto-approved &nbsp;·&nbsp; Doc <strong>#{doc_id}</strong> &nbsp;·&nbsp; All fields above confidence threshold
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="result-banner banner-warning">
                                    ⚠️ Sent to review queue &nbsp;·&nbsp; Doc <strong>#{doc_id}</strong> &nbsp;·&nbsp; {flagged} field(s) flagged
                                </div>""", unsafe_allow_html=True)

                            # ── KPI cards ──
                            st.markdown(f"""
                            <div class="kpi-grid">
                                <div class="kpi-card">
                                    <div class="kpi-label">Vendor</div>
                                    <div class="kpi-value" style="font-size:1.1rem">{summary.get("vendor") or "—"}</div>
                                </div>
                                <div class="kpi-card">
                                    <div class="kpi-label">Total Amount</div>
                                    <div class="kpi-value accent">{summary.get("currency") or ""} {(summary.get("total") or 0):,.2f}</div>
                                </div>
                                <div class="kpi-card">
                                    <div class="kpi-label">Invoice Number</div>
                                    <div class="kpi-value" style="font-size:1.1rem">{summary.get("invoice_number") or "—"}</div>
                                </div>
                                <div class="kpi-card">
                                    <div class="kpi-label">Date</div>
                                    <div class="kpi-value" style="font-size:1.1rem">{summary.get("date") or "—"}</div>
                                </div>
                                <div class="kpi-card">
                                    <div class="kpi-label">Line Items</div>
                                    <div class="kpi-value accent">{summary.get("line_items_count", 0)}</div>
                                </div>
                                <div class="kpi-card">
                                    <div class="kpi-label">Confidence</div>
                                    <div class="kpi-value {'green' if conf>=0.75 else 'amber' if conf>=0.5 else 'red'}">{conf:.0%}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # ── Confidence bar ──
                            confidence_bar("Overall Extraction Confidence", conf)

                            # ── Financial breakdown ──
                            with st.expander("💰 Financial Breakdown"):
                                fin_df = pd.DataFrame([
                                    {"Field": "Subtotal", "Value": f"{summary.get('currency','')} {(summary.get('subtotal') or 0):,.2f}"},
                                    {"Field": "Tax",      "Value": f"{summary.get('currency','')} {(summary.get('tax') or 0):,.2f}"},
                                    {"Field": "Total",    "Value": f"{summary.get('currency','')} {(summary.get('total') or 0):,.2f}"},
                                ])
                                st.dataframe(fin_df, hide_index=True, use_container_width=True)

                            # ── Watermarked image ──
                            with st.expander("🖼️ Watermarked Archival Copy"):
                                img_resp = requests.get(f"{API_URL}/processed/{doc_id}", timeout=10)
                                if img_resp.status_code == 200:
                                    st.image(img_resp.content, caption="Stamped with doc ID + timestamp", use_container_width=True)

                        else:
                            st.error(f"Server error {response.status_code}: {response.text}")

                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to backend. Is it running on port 8000?")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")


###############################################################################
# TAB 2 — DOCUMENTS
###############################################################################
with tab2:
    st.markdown('<div class="ll-section-title">Document Archive</div>', unsafe_allow_html=True)
    st.markdown('<div class="ll-section-sub">All processed invoices with search, filter, and sort</div>', unsafe_allow_html=True)

    with st.container():
        f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
        with f1: search_vendor   = st.text_input("Vendor", placeholder="e.g. Acme Ltd", label_visibility="visible")
        with f2: search_filename = st.text_input("Filename", placeholder="invoice.png", label_visibility="visible")
        with f3:
            filter_status = st.selectbox("Status", ["", "uploaded", "processed", "pending_review", "auto_approved", "approved"],
                                         format_func=lambda x: "All statuses" if x == "" else x.replace("_", " ").title())
        with f4: page_size = st.selectbox("Per page", [10, 20, 50], index=0)

        s1, s2, s3 = st.columns([2, 2, 1])
        with s1: sort_by = st.selectbox("Sort by", ["id", "vendor", "filename", "invoice_date", "total"])
        with s2: order   = st.selectbox("Order", ["desc", "asc"])
        with s3: page    = st.number_input("Page", min_value=1, value=1, step=1)

    try:
        resp = requests.get(f"{API_URL}/documents", params=dict(
            vendor=search_vendor, filename=search_filename, status=filter_status,
            page=page, page_size=page_size, sort_by=sort_by, order=order,
        ), timeout=10)

        if resp.status_code == 200:
            result = resp.json()
            docs   = result.get("data", [])

            st.markdown(f"""
            <div style="font-size:0.8rem;color:#6B7280;margin:8px 0 16px 0;">
                Showing page {result['page']} of {result['total_pages']} &nbsp;·&nbsp; <strong style="color:#111827">{result['total']}</strong> total records
            </div>""", unsafe_allow_html=True)

            if docs:
                df = pd.DataFrame(docs)
                # Format columns
                if "overall_confidence" in df.columns:
                    df["confidence_pct"] = (df["overall_confidence"].fillna(0) * 100).round(1).astype(str) + "%"
                if "total" in df.columns:
                    df["total"] = df["total"].apply(lambda x: f"{x:,.2f}" if x else "—")
                if "status" in df.columns:
                    df["status"] = df["status"].apply(lambda x: x.replace("_", " ").title())
                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d %b %Y %H:%M")

                display_cols = [c for c in ["id", "filename", "vendor", "invoice_number",
                                             "invoice_date", "currency", "total",
                                             "confidence_pct", "status", "created_at"] if c in df.columns]
                st.dataframe(
                    df[display_cols].rename(columns={
                        "id": "ID", "filename": "File", "vendor": "Vendor",
                        "invoice_number": "Invoice #", "invoice_date": "Date",
                        "currency": "CCY", "total": "Total",
                        "confidence_pct": "Confidence", "status": "Status",
                        "created_at": "Uploaded",
                    }),
                    hide_index=True,
                    use_container_width=True,
                    height=420,
                )
            else:
                st.info("No documents match your filters.")
        else:
            st.error(f"Failed to load: HTTP {resp.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")


###############################################################################
# TAB 3 — REVIEW QUEUE
###############################################################################
with tab3:
    st.markdown('<div class="ll-section-title">Human Review Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="ll-section-sub">Fields below the 0.75 confidence threshold require manual correction before approval</div>', unsafe_allow_html=True)

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("↺  Refresh", key="refresh_review"):
            st.rerun()

    try:
        resp = requests.get(f"{API_URL}/review", timeout=10)
        if resp.status_code != 200:
            st.error(f"Failed to load review queue: {resp.status_code}")
        else:
            queue = resp.json()
            docs  = queue.get("documents", [])
            total = queue.get("total", 0)

            if total == 0:
                st.markdown("""
                <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:24px 28px;text-align:center;margin-top:20px">
                    <div style="font-size:2rem;margin-bottom:8px">✅</div>
                    <div style="font-weight:700;color:#166534;font-size:1.1rem">Review queue is empty</div>
                    <div style="color:#4ADE80;font-size:0.85rem;margin-top:4px">All documents have been auto-approved or manually reviewed</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:12px 18px;margin-bottom:20px;color:#92400E;font-weight:600;font-size:0.9rem">
                    ⏳ {total} document(s) awaiting review
                </div>""", unsafe_allow_html=True)

                for doc in docs:
                    conf = doc.get("overall_confidence") or 0
                    conf_color = "#059669" if conf >= 0.75 else "#D97706" if conf >= 0.5 else "#DC2626"

                    with st.expander(
                        f"📄 Doc #{doc['id']}  ·  {doc.get('vendor') or 'Unknown Vendor'}  ·  {doc.get('invoice_date') or 'No date'}  ·  Confidence: {conf:.0%}",
                        expanded=(total == 1),
                    ):
                        # Flagged fields table
                        flagged = doc.get("flagged_fields", [])
                        if flagged:
                            st.markdown("**⚠️ Flagged fields** *(confidence below threshold)*")
                            flag_df = pd.DataFrame(flagged)
                            flag_df["confidence"] = (flag_df["confidence"] * 100).round(1).astype(str) + "%"
                            st.dataframe(flag_df, hide_index=True, use_container_width=True)

                        st.markdown("---")
                        st.markdown("**✏️ Correct extracted values**")

                        c1, c2 = st.columns(2)
                        with c1:
                            vendor   = st.text_input("Vendor",     value=doc.get("vendor") or "",          key=f"vendor_{doc['id']}")
                            inv_num  = st.text_input("Invoice #",   value=doc.get("invoice_number") or "",  key=f"invnum_{doc['id']}")
                            inv_date = st.text_input("Date (YYYY-MM-DD)", value=doc.get("invoice_date") or "", key=f"date_{doc['id']}")
                            currency = st.text_input("Currency",   value=doc.get("currency") or "",         key=f"curr_{doc['id']}")
                        with c2:
                            subtotal  = st.number_input("Subtotal",  value=float(doc.get("subtotal") or 0),  key=f"sub_{doc['id']}")
                            tax       = st.number_input("Tax",       value=float(doc.get("tax") or 0),       key=f"tax_{doc['id']}")
                            total_val = st.number_input("Total",     value=float(doc.get("total") or 0),     key=f"total_{doc['id']}")
                            new_conf  = st.slider("Confidence", 0.0, 1.0, float(conf), key=f"conf_{doc['id']}")

                        new_status = st.selectbox("Set status after review",
                                                   ["approved", "pending_review"], index=0,
                                                   key=f"status_{doc['id']}")

                        # Watermarked preview
                        img_resp = requests.get(f"{API_URL}/processed/{doc['id']}", timeout=10)
                        if img_resp.status_code == 200:
                            st.image(img_resp.content, caption="Watermarked archival copy", use_container_width=True)

                        if st.button(f"✅  Approve Doc #{doc['id']}", key=f"approve_{doc['id']}"):
                            payload = {
                                "vendor": vendor, "invoice_number": inv_num,
                                "invoice_date": inv_date, "currency": currency,
                                "subtotal": subtotal, "tax": tax, "total": total_val,
                                "overall_confidence": new_conf, "status": new_status,
                            }
                            approve_resp = requests.post(f"{API_URL}/approve/{doc['id']}", json=payload, timeout=10)
                            if approve_resp.status_code == 200:
                                st.success(f"✅ Doc #{doc['id']} approved!")
                                st.rerun()
                            else:
                                st.error(f"Failed: {approve_resp.text}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")


###############################################################################
# TAB 4 — DASHBOARD
###############################################################################
with tab4:
    header_col1, header_col2 = st.columns([5, 1])
    with header_col1:
        st.markdown('<div class="ll-section-title">Dashboard Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="ll-section-sub">Real-time performance and financial metrics for your extraction pipeline</div>', unsafe_allow_html=True)
    with header_col2:
        if st.button("↺  Refresh", key="refresh_dash", use_container_width=True):
            st.rerun()

    try:
        resp = requests.get(f"{API_URL}/dashboard", timeout=10)
        if resp.status_code != 200:
            st.error("Unable to load dashboard stats.")
        else:
            d = resp.json()
            total_docs = max(d["total_documents"], 1)
            auto_rate = d["auto_approved"] / total_docs * 100

            # ── Section 1: Extraction Pipeline ──
            st.markdown('<div style="font-weight:700; color:#374151; margin-bottom:12px; font-size:0.9rem; text-transform:uppercase; letter-spacing:0.05em;">⚡ Extraction Pipeline</div>', unsafe_allow_html=True)
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Documents</div>
                    <div class="kpi-value">{d["total_documents"]}</div>
                    <div style="font-size:0.7rem; color:#6B7280; margin-top:4px;">All time uploads</div>
                </div>""", unsafe_allow_html=True)
            with p2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Auto-Approved</div>
                    <div class="kpi-value green">{d["auto_approved"]}</div>
                    <div style="font-size:0.7rem; color:#059669; margin-top:4px;">{auto_rate:.0f}% success rate</div>
                </div>""", unsafe_allow_html=True)
            with p3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Pending Review</div>
                    <div class="kpi-value amber">{d["pending_review"]}</div>
                    <div style="font-size:0.7rem; color:#D97706; margin-top:4px;">Manual action required</div>
                </div>""", unsafe_allow_html=True)
            with p4:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Processed Today</div>
                    <div class="kpi-value accent">{d["today_uploads"]}</div>
                    <div style="font-size:0.7rem; color:#6366F1; margin-top:4px;">Active volume</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            # ── Section 2: Financial & Quality ──
            st.markdown('<div style="font-weight:700; color:#374151; margin-bottom:12px; font-size:0.9rem; text-transform:uppercase; letter-spacing:0.05em;">💰 Financial & Quality Overview</div>', unsafe_allow_html=True)
            f1, f2, f3 = st.columns(3)
            with f1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Invoice Value</div>
                    <div class="kpi-value accent" style="font-size:1.3rem">₹ {d['total_invoice_amount']:,.2f}</div>
                    <div style="font-size:0.7rem; color:#6B7280; margin-top:4px;">Cumulative across documents</div>
                </div>""", unsafe_allow_html=True)
            with f2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Avg Confidence</div>
                    <div class="kpi-value {'green' if d['average_confidence']>=0.75 else 'amber'}">{d['average_confidence']:.1%}</div>
                    <div style="font-size:0.7rem; color:#6B7280; margin-top:4px;">AI extraction reliability</div>
                </div>""", unsafe_allow_html=True)
            with f3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Human-Reviewed</div>
                    <div class="kpi-value">{d["approved"]}</div>
                    <div style="font-size:0.7rem; color:#6B7280; margin-top:4px;">Documents verified by staff</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<hr/>", unsafe_allow_html=True)

            chart_l, chart_r = st.columns(2, gap="large")

            # ── Pie: status distribution ──
            with chart_l:
                st.markdown("**Document Status Distribution**")
                status_resp = requests.get(f"{API_URL}/dashboard/status", timeout=10)
                if status_resp.status_code == 200 and status_resp.json():
                    sd = status_resp.json()
                    labels = [x["status"].replace("_", " ").title() for x in sd]
                    values = [x["count"] for x in sd]
                    palette = ["#6366F1", "#10B981", "#F59E0B", "#3B82F6", "#EC4899"]

                    fig, ax = plt.subplots(figsize=(4, 3.5), facecolor="none")
                    wedges, texts, autotexts = ax.pie(
                        values, labels=labels, autopct="%1.0f%%",
                        colors=palette[:len(labels)],
                        startangle=90,
                        textprops={"fontsize": 8, "color": "#374151", "fontfamily": "sans-serif"},
                        wedgeprops={"linewidth": 2, "edgecolor": "white"},
                    )
                    for at in autotexts:
                        at.set_color("white")
                        at.set_fontweight("bold")
                        at.set_fontsize(8)
                    ax.set_facecolor("none")
                    st.pyplot(fig, transparent=True)
                    plt.close(fig)
                else:
                    st.info("No data yet.")

            # ── Bar: daily uploads ──
            with chart_r:
                st.markdown("**Daily Upload Activity**")
                daily_resp = requests.get(f"{API_URL}/dashboard/daily", timeout=10)
                if daily_resp.status_code == 200 and daily_resp.json():
                    dd = daily_resp.json()
                    daily_df = pd.DataFrame(dd).tail(14)

                    fig2, ax2 = plt.subplots(figsize=(5, 3.5), facecolor="none")
                    ax2.set_facecolor("none")
                    bars = ax2.bar(
                        daily_df["date"], daily_df["count"],
                        color="#6366F1", alpha=0.9,
                        edgecolor="white", linewidth=1.5,
                        width=0.6,
                    )
                    # Value labels on bars
                    for bar in bars:
                        h = bar.get_height()
                        if h > 0:
                            ax2.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                                     str(int(h)), ha="center", va="bottom",
                                     fontsize=8, color="#374151", fontweight="bold")

                    ax2.set_xlabel("Date", color="#9CA3AF", fontsize=8)
                    ax2.set_ylabel("Documents", color="#9CA3AF", fontsize=8)
                    ax2.tick_params(colors="#9CA3AF", labelsize=7)
                    ax2.spines["top"].set_visible(False)
                    ax2.spines["right"].set_visible(False)
                    ax2.spines["left"].set_color("#E5E7EB")
                    ax2.spines["bottom"].set_color("#E5E7EB")
                    ax2.set_ylim(bottom=0)
                    plt.xticks(rotation=35, ha="right")
                    plt.tight_layout()
                    st.pyplot(fig2, transparent=True)
                    plt.close(fig2)
                else:
                    st.info("No upload history yet.")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
