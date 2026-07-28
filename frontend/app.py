"""
LedgerLens Streamlit Frontend

Four-tab layout:
  Tab 1 — 📤 Upload       : Drop invoice image, see extraction with confidence scores
  Tab 2 — 📋 Documents    : Paginated list with search/filter
  Tab 3 — 🔍 Review Queue : st.data_editor for flagged fields, POST /approve
  Tab 4 — 📊 Dashboard    : Metrics cards + status pie + daily bar chart
"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LedgerLens – Invoice AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Premium CSS injection
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    color: #e2e8f0;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Custom header */
.ledgerlens-header {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.ledgerlens-sub {
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 2rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1rem;
    backdrop-filter: blur(10px);
}

/* Confidence badge helper */
.conf-high { color: #4ade80; font-weight: 600; }
.conf-med  { color: #fbbf24; font-weight: 600; }
.conf-low  { color: #f87171; font-weight: 600; }

/* Upload zone */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(99,102,241,0.08) !important;
    border: 2px dashed rgba(99,102,241,0.4) !important;
    border-radius: 16px !important;
}

/* Tab styling */
[data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
[data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
}
[aria-selected="true"] {
    background: rgba(99,102,241,0.25) !important;
    color: #a5b4fc !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
}

/* Info/success/error boxes */
.stSuccess { background: rgba(74,222,128,0.1) !important; border-left: 3px solid #4ade80 !important; }
.stError   { background: rgba(248,113,113,0.1) !important; border-left: 3px solid #f87171 !important; }
.stInfo    { background: rgba(6,182,212,0.1)   !important; border-left: 3px solid #06b6d4 !important; }
.stWarning { background: rgba(251,191,36,0.1)  !important; border-left: 3px solid #fbbf24 !important; }

/* DataFrame / data editor */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.08) !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="ledgerlens-header">🔍 LedgerLens</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ledgerlens-sub">AI-powered invoice extraction · Confidence scoring · Human review queue</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📤 Upload", "📋 Documents", "🔍 Review Queue", "📊 Dashboard"]
)


###############################################################################
# TAB 1 — UPLOAD
###############################################################################
with tab1:
    st.markdown("### Upload Invoice or Receipt")
    st.caption("Supported formats: JPG, JPEG, PNG · Max recommended: 10 MB")

    uploaded_file = st.file_uploader(
        "Drop your invoice here",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        col_img, col_result = st.columns([1, 1], gap="large")

        with col_img:
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

        with col_result:
            if st.button("⚡ Extract Invoice Data", use_container_width=True):
                with st.spinner("Running moderation gate → GPT-4o extraction…"):
                    try:
                        response = requests.post(
                            f"{API_URL}/ingest",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                            timeout=120,
                        )

                        if response.status_code == 422:
                            err = response.json().get("detail", {})
                            if isinstance(err, dict) and err.get("error") == "moderation_blocked":
                                st.error(
                                    f"🚫 **Image blocked by content moderation**\n\n"
                                    f"Reason: `{err.get('blocked_reason', 'policy violation')}`"
                                )
                            else:
                                st.error(f"Validation error: {response.text}")

                        elif response.status_code == 200:
                            data = response.json()
                            summary = data.get("extraction_summary", {})
                            flagged = data.get("flagged_count", 0)
                            doc_status = data.get("status", "")

                            # Status banner
                            if doc_status == "auto_approved":
                                st.success(f"✅ **Auto-approved** — Doc ID: `{data['document_id']}`")
                            else:
                                st.warning(
                                    f"⚠️ **Sent to review queue** — Doc ID: `{data['document_id']}`  \n"
                                    f"{flagged} field(s) below confidence threshold"
                                )

                            st.divider()

                            # Key metrics row
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Vendor", summary.get("vendor") or "—")
                            m2.metric("Total", f"{summary.get('currency') or ''} {summary.get('total') or 0:.2f}")
                            m3.metric(
                                "Confidence",
                                f"{(summary.get('overall_confidence') or 0):.0%}",
                            )

                            m4, m5, m6 = st.columns(3)
                            m4.metric("Invoice #", summary.get("invoice_number") or "—")
                            m5.metric("Date", summary.get("date") or "—")
                            m6.metric("Line Items", summary.get("line_items_count", 0))

                            st.divider()

                            # Confidence bar
                            conf = summary.get("overall_confidence", 0)
                            conf_color = (
                                "#4ade80" if conf >= 0.75
                                else "#fbbf24" if conf >= 0.5
                                else "#f87171"
                            )
                            st.markdown(f"**Extraction Confidence**")
                            st.progress(conf)

                            # Financial breakdown
                            with st.expander("💰 Financial Breakdown"):
                                fin_df = pd.DataFrame([
                                    {"Field": "Subtotal", "Value": summary.get("subtotal")},
                                    {"Field": "Tax", "Value": summary.get("tax")},
                                    {"Field": "Total", "Value": summary.get("total")},
                                ])
                                st.dataframe(fin_df, hide_index=True, use_container_width=True)

                            # View watermarked image
                            doc_id = data["document_id"]
                            with st.expander("🖼️ View Watermarked Image"):
                                img_resp = requests.get(f"{API_URL}/processed/{doc_id}", timeout=10)
                                if img_resp.status_code == 200:
                                    st.image(img_resp.content, caption="Watermarked for archival", use_container_width=True)

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
    st.markdown("### Document Archive")

    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        search_vendor = st.text_input("Search vendor", placeholder="e.g. Acme Ltd")
    with f2:
        search_filename = st.text_input("Search filename", placeholder="invoice.png")
    with f3:
        filter_status = st.selectbox(
            "Status",
            ["", "uploaded", "processed", "pending_review", "auto_approved", "approved"],
            format_func=lambda x: "All statuses" if x == "" else x,
        )
    with f4:
        page_size = st.selectbox("Per page", [10, 20, 50], index=0)

    s1, s2, s3 = st.columns([2, 2, 1])
    with s1:
        sort_by = st.selectbox("Sort by", ["id", "vendor", "filename", "invoice_date", "total"])
    with s2:
        order = st.selectbox("Order", ["desc", "asc"])
    with s3:
        page = st.number_input("Page", min_value=1, value=1, step=1)

    params = dict(
        vendor=search_vendor, filename=search_filename, status=filter_status,
        page=page, page_size=page_size, sort_by=sort_by, order=order,
    )

    try:
        resp = requests.get(f"{API_URL}/documents", params=params, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            st.caption(f"Showing page {result['page']} of {result['total_pages']} — {result['total']} total records")
            docs = result.get("data", [])
            if docs:
                df = pd.DataFrame(docs)
                display_cols = [c for c in [
                    "id", "filename", "vendor", "invoice_number",
                    "invoice_date", "currency", "total", "overall_confidence", "status", "created_at"
                ] if c in df.columns]
                # Color-code confidence
                st.dataframe(
                    df[display_cols],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "overall_confidence": st.column_config.ProgressColumn(
                            "Confidence", min_value=0, max_value=1, format="%.0%%"
                        ),
                        "total": st.column_config.NumberColumn("Total", format="%.2f"),
                        "id": st.column_config.NumberColumn("ID", width="small"),
                    },
                )
            else:
                st.info("No documents found matching your filters.")
        else:
            st.error(f"Failed to load documents: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")


###############################################################################
# TAB 3 — REVIEW QUEUE
###############################################################################
with tab3:
    st.markdown("### 🔍 Human Review Queue")
    st.caption("Fields below the 0.75 confidence threshold are sent here for correction.")

    if st.button("🔄 Refresh Queue", key="refresh_review"):
        st.rerun()

    try:
        resp = requests.get(f"{API_URL}/review", timeout=10)
        if resp.status_code != 200:
            st.error(f"Failed to load review queue: {resp.status_code}")
        else:
            queue = resp.json()
            docs = queue.get("documents", [])
            total = queue.get("total", 0)

            if total == 0:
                st.success("✅ Review queue is empty — all documents auto-approved!")
            else:
                st.warning(f"**{total}** document(s) awaiting review")

                for doc in docs:
                    with st.expander(
                        f"📄 Doc #{doc['id']} — {doc.get('vendor') or 'Unknown Vendor'} "
                        f"· {doc.get('invoice_date') or 'No date'} "
                        f"· Confidence: {(doc.get('overall_confidence') or 0):.0%}",
                        expanded=(total == 1),
                    ):
                        # Show flagged fields
                        flagged = doc.get("flagged_fields", [])
                        if flagged:
                            st.markdown("**⚠️ Flagged fields:**")
                            flag_df = pd.DataFrame(flagged)
                            st.dataframe(
                                flag_df,
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "confidence": st.column_config.ProgressColumn(
                                        "Confidence", min_value=0, max_value=1, format="%.0%%"
                                    )
                                },
                            )

                        st.divider()
                        st.markdown("**✏️ Correct extracted values:**")

                        # Editable fields
                        c1, c2 = st.columns(2)
                        with c1:
                            vendor = st.text_input("Vendor", value=doc.get("vendor") or "", key=f"vendor_{doc['id']}")
                            inv_num = st.text_input("Invoice #", value=doc.get("invoice_number") or "", key=f"invnum_{doc['id']}")
                            inv_date = st.text_input("Date", value=doc.get("invoice_date") or "", key=f"date_{doc['id']}")
                            currency = st.text_input("Currency", value=doc.get("currency") or "", key=f"curr_{doc['id']}")
                        with c2:
                            subtotal = st.number_input("Subtotal", value=float(doc.get("subtotal") or 0), key=f"sub_{doc['id']}")
                            tax = st.number_input("Tax", value=float(doc.get("tax") or 0), key=f"tax_{doc['id']}")
                            total_val = st.number_input("Total", value=float(doc.get("total") or 0), key=f"total_{doc['id']}")
                            confidence = st.slider(
                                "Confidence", 0.0, 1.0,
                                float(doc.get("overall_confidence") or 0),
                                key=f"conf_{doc['id']}"
                            )

                        new_status = st.selectbox(
                            "Set status",
                            ["pending_review", "approved"],
                            index=1,
                            key=f"status_{doc['id']}",
                        )

                        # Watermarked image preview
                        img_resp = requests.get(f"{API_URL}/processed/{doc['id']}", timeout=10)
                        if img_resp.status_code == 200:
                            st.image(img_resp.content, caption="Watermarked image", use_container_width=True)

                        if st.button(f"✅ Approve Doc #{doc['id']}", key=f"approve_{doc['id']}"):
                            payload = {
                                "vendor": vendor, "invoice_number": inv_num,
                                "invoice_date": inv_date, "currency": currency,
                                "subtotal": subtotal, "tax": tax, "total": total_val,
                                "overall_confidence": confidence, "status": new_status,
                            }
                            approve_resp = requests.post(
                                f"{API_URL}/approve/{doc['id']}", json=payload, timeout=10
                            )
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
    st.markdown("### 📊 Dashboard")

    if st.button("🔄 Refresh", key="refresh_dash"):
        st.rerun()

    try:
        resp = requests.get(f"{API_URL}/dashboard", timeout=10)
        if resp.status_code != 200:
            st.error("Unable to load dashboard stats.")
        else:
            d = resp.json()

            # Top-level KPIs
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📄 Total Docs", d["total_documents"])
            c2.metric("⏳ Pending Review", d["pending_review"])
            c3.metric("✅ Auto-Approved", d["auto_approved"])
            c4.metric("👤 Approved", d["approved"])
            c5.metric("📅 Today", d["today_uploads"])

            st.divider()

            c6, c7, c8 = st.columns(3)
            c6.metric("Avg Confidence", f"{d['average_confidence']:.1%}")
            c7.metric("Total Invoice Value", f"₹ {d['total_invoice_amount']:,.2f}")
            auto_rate = (
                d["auto_approved"] / max(d["total_documents"], 1) * 100
            )
            c8.metric("Auto-Approval Rate", f"{auto_rate:.1f}%")

            st.divider()

            chart_left, chart_right = st.columns(2)

            # Pie chart — status distribution
            with chart_left:
                st.markdown("**Document Status Distribution**")
                status_resp = requests.get(f"{API_URL}/dashboard/status", timeout=10)
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if status_data:
                        labels = [x["status"] for x in status_data]
                        values = [x["count"] for x in status_data]
                        colors = ["#6366f1", "#4ade80", "#f87171", "#fbbf24", "#06b6d4"]
                        fig, ax = plt.subplots(figsize=(4, 4), facecolor="none")
                        ax.set_facecolor("none")
                        wedges, texts, autotexts = ax.pie(
                            values, labels=labels, autopct="%1.0f%%",
                            colors=colors[:len(labels)], startangle=90,
                            textprops={"color": "#e2e8f0", "fontsize": 9},
                        )
                        for at in autotexts:
                            at.set_color("#1a1a2e")
                            at.set_fontweight("bold")
                        st.pyplot(fig, transparent=True)
                    else:
                        st.info("No data yet.")

            # Bar chart — daily uploads
            with chart_right:
                st.markdown("**Daily Uploads (Last 14 Days)**")
                daily_resp = requests.get(f"{API_URL}/dashboard/daily", timeout=10)
                if daily_resp.status_code == 200:
                    daily_data = daily_resp.json()
                    if daily_data:
                        daily_df = pd.DataFrame(daily_data).tail(14)
                        fig2, ax2 = plt.subplots(figsize=(5, 4), facecolor="none")
                        ax2.set_facecolor("none")
                        bars = ax2.bar(
                            daily_df["date"], daily_df["count"],
                            color="#6366f1", alpha=0.85, edgecolor="#8b5cf6", linewidth=0.5,
                        )
                        ax2.set_xlabel("Date", color="#94a3b8", fontsize=8)
                        ax2.set_ylabel("Documents", color="#94a3b8", fontsize=8)
                        ax2.tick_params(colors="#94a3b8", labelsize=7)
                        plt.xticks(rotation=45, ha="right")
                        ax2.spines[:].set_color("#334155")
                        st.pyplot(fig2, transparent=True)
                    else:
                        st.info("No upload history yet.")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
