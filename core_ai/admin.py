import streamlit as st
import pandas as pd
import time
from datetime import datetime, date, time as dt_time
from supabase import create_client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="Smart Parking Admin", layout="wide", page_icon="🔐")

st.markdown("""
    <style>
    /* Admin Theme: Light Background */
    .stApp { background-color: #f8fafc; }
    
    /* Custom Metric Cards with Sparkline Mockups */
    .metric-container { display: flex; justify-content: space-between; background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-val { font-size: 28px; font-weight: bold; color: #1e293b; margin-top: 5px; }
    .metric-label { font-size: 13px; color: #64748b; font-weight: 500;}
    .sparkline { font-size: 20px; font-weight: bold; }
    
    /* Purple Headers & Buttons */
    .admin-header { background-color: #8b5cf6; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(139, 92, 246, 0.2); }
    .stButton>button { background-color: #8b5cf6; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: bold; width: 100%; transition: all 0.3s;}
    .stButton>button:hover { background-color: #7c3aed; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }
    
    /* Login Box */
    .login-box { max-width: 450px; margin: 100px auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .error-box { background-color: #fee2e2; color: #b91c1c; padding: 15px; border-radius: 8px; margin-top: 15px; font-size: 14px; }
    
    /* CCTV Stream View */
    .cctv-container { background-color: #111827; border-radius: 12px; padding: 20px; height: 450px; display: flex; flex-direction: column; justify-content: space-between; position: relative;}
    .cctv-live-badge { position: absolute; top: 15px; right: 20px; color: #ef4444; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 5px;}
    .cctv-live-dot { width: 8px; height: 8px; background-color: #ef4444; border-radius: 50%; animation: pulse 1.5s infinite; }
    .cctv-timestamp { color: white; font-size: 12px; background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px; width: fit-content;}
    .cctv-center-text { text-align: center; color: #64748b; margin-top: 100px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    
    /* Settings Cards */
    .settings-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION & ERROR HANDLING ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    st.error("Missing Streamlit Secrets. Please configure Supabase URL and Key.")
    st.stop()

def get_cloud_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        # Prevents the app from crashing and tells you exactly what's wrong!
        st.error(f"Database Error: Could not find table '{table_name}'. Please ensure it exists in Supabase.")
        return pd.DataFrame()

# --- 3. AUTHENTICATION LOGIC ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1e293b; margin-bottom: 5px;'>Sign in to manage the facility</h3>", unsafe_allow_html=True)
    
    username = st.text_input("Username", value="Admin001")
    password = st.text_input("Password", type="password")
    
    if st.button("Secure Login"):
        if username == "Admin001" and password == "hello_admin1":
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.markdown("<div class='error-box'>Invalid credentials. Please try again.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. ADMIN SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2764/2764359.png", width=60)
    st.title("Admin Console")
    st.markdown("---")
    menu_selection = st.radio("Navigation", ["🔍 Parking Monitoring", "⚙️ Settings & Configuration", "📊 Generate Reports"])
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

# --- 5. PAGE: PARKING MONITORING ---
if menu_selection == "🔍 Parking Monitoring":
    df_slots = get_cloud_data("slots")
    
    total = len(df_slots)
    occupied = len(df_slots[df_slots['status'] == 'Occupied']) if not df_slots.empty else 0
    available = total - occupied
    occ_rate = int((occupied / total) * 100) if total > 0 else 0
    
    # Custom HTML Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-container'><div><div class='metric-label'>Total Spaces</div><div class='metric-val'>{total}</div></div><div class='sparkline' style='color:#3b82f6;'>∿</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-container'><div><div class='metric-label'>Available</div><div class='metric-val'>{available}</div></div><div class='sparkline' style='color:#10b981;'>∿</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-container'><div><div class='metric-label'>Occupied</div><div class='metric-val'>{occupied}</div></div><div class='sparkline' style='color:#ef4444;'>∿</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-container'><div><div class='metric-label'>Occupancy</div><div class='metric-val'>{occ_rate}%</div></div><div class='sparkline' style='color:#8b5cf6;'>∿</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br><p style='color:#64748b; font-size:14px; margin-bottom: 5px;'>View Mode</p>", unsafe_allow_html=True)
    view_mode = st.radio("", ["Grid View", "CCTV Stream View"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    # --- GRID VIEW ---
    if view_mode == "Grid View":
        st.markdown("""
        <div style="display:flex; gap: 15px; font-size: 13px; margin-bottom: 20px;">
            <div><span style='color:#10b981'>■</span> Available</div>
            <div><span style='color:#ef4444'>■</span> Occupied</div>
            <div><span style='color:#3b82f6'>■</span> Disabled</div>
            <div><span style='color:#14b8a6'>■</span> EV Charging</div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Grid rendering goes here (uses the same HTML logic as your main app).")
            
    # --- CCTV STREAM VIEW ---
    elif view_mode == "CCTV Stream View":
        lc, rc = st.columns([3, 7])
        with lc:
            st.markdown("##### Camera Feeds")
            wings = sorted(df_slots['wing_id'].unique()) if not df_slots.empty else ["Level 1", "Level 2", "Level 3"]
            selected_cam = st.radio("Select Camera", wings, label_visibility="collapsed")
            
        with rc:
            st.markdown(f"##### {selected_cam}")
            now_str = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
            cctv_html = f"""
            <div class='cctv-container'>
                <div class='cctv-live-badge'><div class='cctv-live-dot'></div> LIVE</div>
                <div class='cctv-timestamp'>{now_str}</div>
                <div class='cctv-center-text'>
                    <h1 style='color: #475569; margin-bottom: 0;'>📹</h1>
                    <p style='margin:0;'>Live CCTV Feed</p>
                    <small>Camera: {selected_cam}</small>
                </div>
                <div style='background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 4px; color: white; width: fit-content; font-size: 12px;'>
                    {selected_cam} - Main View
                </div>
            </div>
            """
            st.markdown(cctv_html, unsafe_allow_html=True)

# --- 6. PAGE: SETTINGS & MANAGEMENT ---
elif menu_selection == "⚙️ Settings & Configuration":
    st.markdown("<div class='admin-header'><h2 style='margin:0;'>Settings & Configuration</h2><p style='margin:0; opacity: 0.9;'>Manage parking fees and facility information</p></div>", unsafe_allow_html=True)
    
    # FETCH CURRENT FEES FROM CLOUD (Using parking_fee table)
    try:
        settings_res = supabase.table("parking_fee").select("*").eq("id", 1).execute()
        current_settings = settings_res.data[0] if settings_res.data else {"base_fee": 2.0, "rate_per_second": 0.1}
    except:
        current_settings = {"base_fee": 2.0, "rate_per_second": 0.1}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("#### ⏱️ Parking Fee Structure (Demo Mode)")
        st.caption("Fees are synced to the cloud and update the live user dashboard instantly.")
        
        base_fee = st.number_input("Base Rate (RM per entry)", value=float(current_settings['base_fee']), step=0.50)
        sec_fee = st.number_input("Rate per Second Parked (RM)", value=float(current_settings['rate_per_second']), step=0.05)
        
        st.markdown(f"<div style='margin-top: 15px; padding: 10px; background-color: #f3f4f6; border-radius: 5px;'><strong>Demo Calculation Preview:</strong><br>A car parked for 30 seconds will cost: RM {base_fee + (30 * sec_fee):.2f}</div>", unsafe_allow_html=True)
        
        if st.button("💾 Save Demo Fee Structure"):
            try:
                # PUSH NEW FEES TO CLOUD
                supabase.table("parking_fee").upsert({"id": 1, "base_fee": base_fee, "rate_per_second": sec_fee}).execute()
                st.success("✅ Fees successfully synced to Cloud Database! Users will now be charged this rate.")
            except Exception as e:
                st.error("Failed to save. Please check your Supabase connection.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("#### 📍 Facility Information")
        st.text_input("Facility Name", value="Smart Parking Center")
        st.text_input("Address", value="123 Main Street, City Center")
        st.text_input("Total Levels", value="3")
        st.text_input("Operating Hours", value="24/7")
        st.button("💾 Save Facility Info")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. PAGE: GENERATE REPORTS ---
elif menu_selection == "📊 Generate Reports":
    st.markdown("<div class='admin-header'><h2 style='margin:0;'>Generate Reports</h2><p style='margin:0; opacity: 0.9;'>Analyze parking data and generate detailed reports</p></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
    st.markdown("##### 📅 Select Report Period")
    
    c1, c2 = st.columns(2)
    with c1: 
        start_date = st.date_input("Start Date", value=date.today())
        start_time = st.time_input("Start Time", value=dt_time(0, 0))
    with c2: 
        end_date = st.date_input("End Date", value=date.today())
        end_time = st.time_input("End Time", value=dt_time(23, 59))
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📈 Fetch Transactions from Cloud"):
        df_history = get_cloud_data("transactions")
        if not df_history.empty:
            st.dataframe(df_history)
        else:
            st.warning("No data found. Ensure the 'transactions' table exists in Supabase.")
    st.markdown("</div>", unsafe_allow_html=True)
