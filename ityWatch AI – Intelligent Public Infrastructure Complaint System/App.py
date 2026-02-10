import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time
from io import StringIO
import os
import random
import string
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions

# ==========================================
# ⚙️ 1. CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="CityWatch AI | Smart Civic Governance",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# Professional Dark UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161B22; border-radius: 4px; color: #fff; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; }
    div[data-testid="stMetric"] { background-color: #21262D; border: 1px solid #30363D; padding: 15px; border-radius: 8px; }
    .tracking-card { background-color: #1F2937; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; margin-bottom: 20px;}
    .status-Open { color: #EF4444; font-weight: bold; }
    .status-In { color: #F59E0B; font-weight: bold; }
    .status-Resolved { color: #10B981; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ☁️ 2. BACKEND: AZURE STORAGE (WITH SAS TOKENS)
# ==========================================
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
DATA_CONTAINER = "complaint-data"
IMAGE_CONTAINER = "complaint-images"
BLOB_NAME = "complaints_master.csv"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

class AzureBackend:
    def __init__(self):
        try:
            self.service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
            self.data_client = self.service_client.get_blob_client(container=DATA_CONTAINER, blob=BLOB_NAME)
        except Exception as e:
            st.error(f"Azure Connection Failed: {e}")

    def upload_image(self, image_file, tracking_id):
        """Uploads image and returns filename."""
        try:
            filename = f"{tracking_id}_{image_file.name}"
            blob_client = self.service_client.get_blob_client(container=IMAGE_CONTAINER, blob=filename)
            blob_client.upload_blob(image_file, overwrite=True, content_settings=ContentSettings(content_type=image_file.type))
            return filename 
        except Exception as e:
            st.error(f"Image Upload Failed: {e}")
            return None

    def get_image_url(self, blob_name):
        """Generates a SECURE URL (SAS Token) so images are visible."""
        if not isinstance(blob_name, str) or blob_name == "None" or not blob_name.strip():
            return None
        try:
            blob_client = self.service_client.get_blob_client(container=IMAGE_CONTAINER, blob=blob_name)
            
            # Extract Account Key for SAS generation
            account_key = None
            for part in CONNECTION_STRING.split(';'):
                if part.startswith('AccountKey='):
                    account_key = part.replace('AccountKey=', '')
                    break
            
            if not account_key: return blob_client.url

            # Generate Token (Valid 1 hour)
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=IMAGE_CONTAINER,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1)
            )
            return f"{blob_client.url}?{sas_token}"
        except Exception:
            return None

    def get_schema(self):
        return [
            "tracking_id", "timestamp", "state", "city", "area", 
            "category", "severity_reported", "description", 
            "image_ref", "status", "admin_remarks",
            "ai_category", "ai_severity", "ai_priority_score", "ai_confidence", "ai_reasoning",
            "cluster_flag" 
        ]

    def load_data(self):
        try:
            if not self.data_client.exists(): return pd.DataFrame(columns=self.get_schema())
            stream = self.data_client.download_blob()
            csv_text = stream.readall().decode('utf-8')
            if not csv_text.strip(): return pd.DataFrame(columns=self.get_schema())
            df = pd.read_csv(StringIO(csv_text))
            
            # Sanitization
            for col in self.get_schema():
                if col not in df.columns:
                    if col == 'ai_priority_score': df[col] = 0
                    elif col == 'cluster_flag': df[col] = False
                    elif col == 'image_ref': df[col] = "None"
                    else: df[col] = "Unknown"
            
            # Ensure types
            if 'image_ref' in df.columns: df['image_ref'] = df['image_ref'].fillna("None").astype(str)
            df['ai_priority_score'] = pd.to_numeric(df['ai_priority_score'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception:
            return pd.DataFrame(columns=self.get_schema())

    def save_data(self, df):
        try:
            output = StringIO()
            df.to_csv(output, index=False)
            self.data_client.upload_blob(output.getvalue(), overwrite=True)
            return True
        except Exception as e:
            st.error(f"Save Failed: {e}")
            return False

# ==========================================
# 🧠 3. AI ENGINE
# ==========================================
class AIEngine:
    @staticmethod
    def generate_tracking_id():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    @staticmethod
    def analyze_complaint(description, category, severity):
        desc_lower = description.lower()
        keywords = {
            "Water": ["leak", "pipe", "dirty", "supply", "water"],
            "Road": ["pothole", "road", "street", "bump"],
            "Electricity": ["wire", "pole", "current", "light", "spark"],
            "Sanitation": ["garbage", "trash", "smell", "waste"]
        }
        detected_cat = category 
        for cat, keys in keywords.items():
            if any(k in desc_lower for k in keys):
                detected_cat = cat
                break
        
        critical_words = ["danger", "death", "fire", "sparking", "flood"]
        is_critical = any(w in desc_lower for w in critical_words)
        ai_severity = "Critical" if is_critical else severity
        
        sev_map = {"Low": 2, "Medium": 5, "High": 8, "Critical": 10}
        base_score = sev_map.get(ai_severity, 5)
        if is_critical: base_score = 10
        
        return {
            "ai_category": detected_cat,
            "ai_severity": ai_severity,
            "priority_score": base_score,
            "reasoning": f"Classified '{detected_cat}'. Severity '{ai_severity}'."
        }

    @staticmethod
    def detect_bursts_and_update_priority(df):
        if df.empty: return df, False
        df['cluster_flag'] = False
        active_mask = df['status'].isin(['Open', 'In Progress'])
        active_df = df[active_mask]
        burst_counts = active_df.groupby(['city', 'category']).size()
        BURST_THRESHOLD = 3 
        updates_made = False
        
        for (city, cat), count in burst_counts.items():
            if count >= BURST_THRESHOLD:
                mask = (df['city'] == city) & (df['category'] == cat) & (df['status'].isin(['Open', 'In Progress']))
                if not df.loc[mask, 'cluster_flag'].all():
                    df.loc[mask, 'ai_severity'] = 'Critical'
                    df.loc[mask, 'ai_priority_score'] = 10
                    df.loc[mask, 'cluster_flag'] = True
                    def update_reasoning(text):
                        if "BURST DETECTED" not in str(text):
                            return str(text) + f" [⚠ AI BURST: {count} reports in {city}]"
                        return text
                    df.loc[mask, 'ai_reasoning'] = df.loc[mask, 'ai_reasoning'].apply(update_reasoning)
                    updates_made = True
                
        return df, updates_made

# ==========================================
# 🏙️ 4. CITIZEN PORTAL
# ==========================================
def render_citizen_portal(backend):
    st.title("🏙️ CityWatch Citizen Services")
    
    # Full Indian State/City Data
    indian_states_cities = {
        "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati"],
        "Arunachal Pradesh": ["Itanagar", "Tawang", "Pasighat"],
        "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat"],
        "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur"],
        "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur"],
        "Goa": ["Panaji", "Margao", "Vasco da Gama"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar", "Gandhidham"],
        "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala"],
        "Himachal Pradesh": ["Shimla", "Dharamshala", "Manali"],
        "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad"],
        "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"],
        "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur"],
        "Madhya Pradesh": ["Indore", "Bhopal", "Gwalior", "Jabalpur", "Ujjain"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Thane"],
        "Manipur": ["Imphal", "Thoubal"],
        "Meghalaya": ["Shillong", "Tura"],
        "Mizoram": ["Aizawl", "Lunglei"],
        "Nagaland": ["Kohima", "Dimapur"],
        "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Puri"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Chandigarh"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
        "Sikkim": ["Gangtok", "Namchi"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
        "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
        "Tripura": ["Agartala", "Udaipur"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida", "Deoria", "Ghaziabad"],
        "Uttarakhand": ["Dehradun", "Haridwar", "Rishikesh", "Nainital"],
        "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Durgapur"],
        "Delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
        "Jammu and Kashmir": ["Srinagar", "Jammu"],
        "Ladakh": ["Leh", "Kargil"],
        "Puducherry": ["Puducherry", "Karaikal"]
    }

    tab1, tab2 = st.tabs(["📢 File a Complaint", "🔍 Track Status"])
    
    with tab1:
        st.markdown("### Report a Civic Issue")
        c1, c2 = st.columns(2)
        with c1:
            sel_state = st.selectbox("State", list(indian_states_cities.keys()))
            sel_city = st.selectbox("City", indian_states_cities[sel_state])
        with c2:
            sel_cat = st.selectbox("Category", ["Road", "Water", "Electricity", "Sanitation", "Traffic", "Safety", "Internet", "Other"])
            sel_sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])

        with st.form("complaint_form", clear_on_submit=True):
            sel_area = st.text_input("Area / Locality", placeholder="e.g. Sector 5, Main Market")
            desc = st.text_area("Problem Description", height=120)
            uploaded_file = st.file_uploader("Upload Image (Optional)", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("🚀 Submit Complaint")
            
            if submitted:
                if not sel_area or not desc:
                    st.error("Please fill in the Area and Description fields.")
                else:
                    with st.spinner("Processing..."):
                        track_id = AIEngine.generate_tracking_id()
                        img_ref = "None"
                        if uploaded_file:
                            img_ref = backend.upload_image(uploaded_file, track_id)
                        
                        ai_result = AIEngine.analyze_complaint(desc, sel_cat, sel_sev)
                        
                        new_record = {
                            "tracking_id": track_id,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "state": sel_state, "city": sel_city, "area": sel_area,
                            "category": sel_cat, "severity_reported": sel_sev, "description": desc,
                            "image_ref": img_ref, "status": "Open", "admin_remarks": "",
                            "ai_category": ai_result['ai_category'], "ai_severity": ai_result['ai_severity'],
                            "ai_priority_score": ai_result['priority_score'], "ai_confidence": 0.9,
                            "ai_reasoning": ai_result['reasoning'], "cluster_flag": False
                        }
                        
                        df = backend.load_data()
                        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                        backend.save_data(df)
                        
                        st.success("Complaint Registered Successfully!")
                        st.markdown(f"""
                            <div style="background-color: #059669; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                                <h2>Tracking ID: {track_id}</h2>
                            </div>
                        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Track Your Complaint")
        track_input = st.text_input("Enter 8-Digit Tracking ID", max_chars=8).upper()
        
        if st.button("Search Record"):
            df = backend.load_data()
            if "tracking_id" in df.columns:
                record = df[df['tracking_id'] == track_input]
                if not record.empty:
                    r = record.iloc[0]
                    status_color = "#EF4444" if r['status'] == "Open" else "#10B981"
                    st.markdown(f"""
                    <div class="tracking-card">
                        <h2 style="color: {status_color}">{r['status']}</h2>
                        <p><b>Location:</b> {r['area']}, {r['city']}</p>
                        <p><b>Admin Remarks:</b> {r['admin_remarks'] if pd.notna(r['admin_remarks']) else 'Pending Review'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if r['image_ref'] != "None":
                        img_url = backend.get_image_url(r['image_ref'])
                        if img_url: st.image(img_url, caption="Uploaded Evidence", width=300)
                else:
                    st.error("Tracking ID not found.")

# ==========================================
# 👮‍♂️ 5. ADMIN DASHBOARD (IMPROVED)
# ==========================================
def render_admin_dashboard(backend):
    st.title("🛡️ Authority Command Center")
    
    # 1. Load Data & Run AI
    df = backend.load_data()
    if df.empty:
        st.warning("No data found.")
        return

    df, updated = AIEngine.detect_bursts_and_update_priority(df)
    if updated:
        backend.save_data(df)
        st.toast("⚠️ AI Analysis: High complaint volume detected!", icon="🤖")

    # 2. Tabs
    tab_overview, tab_manage, tab_ai = st.tabs([
        "📊 Insights & Analytics", 
        "📝 Complaint Manager (Cards)", 
        "🧠 AI Intelligence"
    ])

    # --- TAB 1: ANALYTICS ---
    with tab_overview:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Complaints", len(df))
        k2.metric("Critical Issues", len(df[df['ai_severity']=='Critical']), delta_color="inverse")
        k3.metric("Open Cases", len(df[df['status']=='Open']))
        k4.metric("AI Burst Alerts", len(df[df['cluster_flag']==True]))
        
        if not df.empty:
            fig = px.density_heatmap(df, x="city", y="category", title="Complaint Density Heatmap", color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: COMPLAINT MANAGER (CARD VIEW) ---
    with tab_manage:
        # --- FILTERS & SORTING ---
        with st.expander("🔎 Filters & Sorting", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            
            # Get unique values safely
            cities = ["All"] + sorted(df["city"].dropna().unique().tolist())
            cats = ["All"] + sorted(df["category"].dropna().unique().tolist())
            stats = ["All"] + sorted(df["status"].dropna().unique().tolist())
            
            sel_city = c1.selectbox("Filter by City", cities)
            sel_cat = c2.selectbox("Filter by Category", cats)
            sel_stat = c3.selectbox("Filter by Status", stats)
            
            sort_opt = c4.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Priority"])

        # --- APPLY FILTERS ---
        filtered_df = df.copy()
        if sel_city != "All": filtered_df = filtered_df[filtered_df["city"] == sel_city]
        if sel_cat != "All": filtered_df = filtered_df[filtered_df["category"] == sel_cat]
        if sel_stat != "All": filtered_df = filtered_df[filtered_df["status"] == sel_stat]
        
        # --- APPLY SORTING ---
        if sort_opt == "Newest First":
            filtered_df = filtered_df.sort_values(by="timestamp", ascending=False)
        elif sort_opt == "Oldest First":
            filtered_df = filtered_df.sort_values(by="timestamp", ascending=True)
        elif sort_opt == "Highest Priority":
            filtered_df = filtered_df.sort_values(by="ai_priority_score", ascending=False)

        st.markdown(f"**Showing {len(filtered_df)} complaints**")

        # --- RENDER CARDS ---
        # We use enumerate to ensure unique keys for every widget
        for i, (_, row) in enumerate(filtered_df.iterrows()):
            tid = row['tracking_id']
            prio = row['ai_priority_score']
            cat = row['category']
            city = row['city']
            status = row['status']
            
            # Card Header Color
            header = f"[{prio}/10] {cat} in {city} ({status})"
            
            with st.expander(header):
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.markdown(f"**Tracking ID:** `{tid}`")
                    st.markdown(f"**Date:** {row['timestamp']}")
                    st.markdown(f"**Description:** {row['description']}")
                    st.info(f"🤖 **AI Analysis:** {row['ai_reasoning']}")
                    
                    # IMAGE DISPLAY
                    img_ref = row.get("image_ref", "None")
                    if img_ref and img_ref != "None":
                        img_url = backend.get_image_url(img_ref)
                        if img_url:
                            st.image(img_url, caption="Evidence Photo", width=350)
                        else:
                            st.warning("Image reference found, but could not load.")
                
                with col_right:
                    st.markdown("### Actions")
                    # Form for updating status
                    with st.form(f"update_form_{tid}_{i}"):
                        new_stat = st.selectbox("Update Status", ["Open", "In Progress", "Resolved", "Rejected"], index=["Open", "In Progress", "Resolved", "Rejected"].index(status))
                        new_rem = st.text_input("Admin Remarks", value=str(row['admin_remarks']) if pd.notna(row['admin_remarks']) else "")
                        
                        if st.form_submit_button("💾 Update Record"):
                            # Update Main DF
                            df.loc[df['tracking_id'] == tid, 'status'] = new_stat
                            df.loc[df['tracking_id'] == tid, 'admin_remarks'] = new_rem
                            backend.save_data(df)
                            st.success("Updated!")
                            time.sleep(1)
                            st.rerun()

    # --- TAB 3: AI INTELLIGENCE ---
    with tab_ai:
        st.subheader("🤖 AI Logic: Dynamic Severity Analysis")
        st.info("If >3 complaints of the same category occur in one city, AI automatically upgrades them to CRITICAL.")
        
        burst_data = df[df['cluster_flag'] == True]
        if not burst_data.empty:
            st.error(f"🚨 {len(burst_data)} Complaints flagged as BURST EVENTS (High Frequency)")
            st.dataframe(burst_data[['city', 'category', 'description', 'ai_reasoning']], use_container_width=True)
        else:
            st.success("✅ No abnormal complaint spikes detected.")

# ==========================================
# 🚀 6. ROUTER
# ==========================================
def main():
    backend = AzureBackend()
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False

    with st.sidebar:
        st.title("CityWatch AI")
        st.markdown("---")
        mode = st.radio("Access Portal", ["Citizen Services", "Authority Login"])
        st.markdown("---")
        st.caption("Powered by Azure & AI")
    
    if mode == "Citizen Services":
        render_citizen_portal(backend)
    else:
        if st.session_state.is_admin:
            if st.sidebar.button("🔴 Logout"):
                st.session_state.is_admin = False
                st.rerun()
            render_admin_dashboard(backend)
        else:
            st.markdown("<br><br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                with st.form("login_form"):
                    st.subheader("🔒 Secure Access")
                    pwd = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        if pwd == ADMIN_PASSWORD:
                            st.session_state.is_admin = True
                            st.rerun()
                        else:
                            st.error("Access Denied")

if __name__ == "__main__":
    main()