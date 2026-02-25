import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="Smart Parking Admin", layout="wide", page_icon="🔐")

st.markdown("""
    <style>
    /* Admin Theme: Purple & Modern Minimalist */
    .stApp { background-color: #f8fafc; }
    
    /* Login Box */
    .login-box { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #8b5cf6; }
    
    /* Top Metrics */
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    
    /* Purple Headers & Buttons */
    .admin-header { background-color: #8b5cf6; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(139, 92, 246, 0.2); }
    .stButton>button { background-color: #8b5cf6; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: bold; width: 100%; transition: all 0.3s;}
    .stButton>button:hover { background-color: #7c3aed; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }
    
    /* CCTV Stream View */
    .cctv-container { background-color: #0f172a; border-radius: 12px; padding: 20px; height: 500px; display: flex; flex-direction: column; justify-content: space-between; position: relative; border: 1px solid #334155;}
    .cctv-live-badge { position: absolute; top: 15px; right: 20px; color: #ef4444; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 5px;}
    .cctv-live-dot { width: 8px; height: 8px; background-color: #ef4444; border-radius: 50%; animation: pulse 1.5s infinite; }
    .cctv-timestamp { color: #94a3b8; font-size: 12px; font-family: monospace; }
    .cctv-center-text { text-align: center; color: #64748b; margin-top: 150px; }
    
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    
    /* Parking Grid (Reused & Minimized for Admin) */
    .parking-row { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; margin-bottom: 10px;}
    .slot { width: 35px; height: 35px; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .slot.vacant { background-color: #10b981; } .slot.occupied { background-color: #ef4444; } .slot.oku-vacant { background-color: #38bdf8; } .slot.yellow { background-color: #fbbf24; box-shadow: none; }
    .car-icon { font-size: 16px; margin-bottom: 2px; line-height: 1; } .slot-id { font-size: 9px; line-height: 1; }
    
    /* Settings Cards */
    .settings-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .settings-title { display: flex; align-items: center; gap: 10px; color: #1e293b; font-weight: bold; font-size: 18px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
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
        st.error(f"Database Error: Could not find table '{table_name}'. Please ensure it exists.")
        return pd.DataFrame()

# --- 3. AUTHENTICATION LOGIC ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 5px;'>Admin Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 20px;'>Sign in to manage the facility</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter admin username")
    password = st.text_input("Password", type="password", placeholder="Enter password")
    
    if st.button("Secure Login"):
        # FYP Simple Auth
        if username == "admin" and password == "fyp2026":
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop() 

# --- 4. ADMIN SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2764/2764359.png", width=60)
    st.title("Admin Console")
    st.markdown("---")
    menu_selection = st.radio("Navigation", ["🔍 Parking Monitoring", "⚙️ Settings & Configuration", "📊 Generate Reports"])
    st.markdown("---")
    if st.button("🚪 Logout", key="logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

# --- 5. PAGE: PARKING MONITORING ---
if menu_selection == "🔍 Parking Monitoring":
    df_slots = get_cloud_data("slots")
    
    total = len(df_slots)
    occupied = len(df_slots[df_slots['status'] == 'Occupied']) if not df_slots.empty else 0
    available = total - occupied
    occ_rate = int((occupied / total) * 100) if total > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📍 Total Spaces", total)
    m2.metric("🟢 Available", available)
    m3.metric("🔴 Occupied", occupied)
    m4.metric("📈 Occupancy Rate", f"{occ_rate}%")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    view_mode = st.radio("View Mode", ["Grid View", "CCTV Stream View"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    # --- GRID VIEW ---
    if view_mode == "Grid View":
        st.markdown("#### Live Parking Status")
        st.markdown("<span style='color:#10b981'>■ Available</span> &nbsp; <span style='color:#ef4444'>■ Occupied</span> &nbsp; <span style='color:#38bdf8'>■ OKU</span>", unsafe_allow_html=True)
        
        wings = sorted(df_slots['wing_id'].unique()) if not df_slots.empty else []
        for wing in wings:
            st.write(f"**Level: {wing}**")
            wing_data = df_slots[df_slots['wing_id'] == wing].sort_values(by='slot_id')
            
            html = "<div style='background: white; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px;'>"
            html += "<div class='parking-row'>"
            for _, row in wing_data.iterrows():
                status_class = "occupied" if row['status'] == 'Occupied' else "vacant"
                slot_num = row['slot_id'].split('-')[1]
                html += f"<div class='slot {status_class}'><div class='car-icon'>🚗</div><div class='slot-id'>{slot_num}</div></div>"
            html += "</div></div>"
            st.markdown(html, unsafe_allow_html=True)
            
    # --- CCTV STREAM VIEW ---
    elif view_mode == "CCTV Stream View":
        c1, c2 = st.columns([2, 8])
        with c1:
            st.markdown("##### Camera Feeds")
            wings = sorted(df_slots['wing_id'].unique()) if not df_slots.empty else ["W1", "W3A", "W5", "W7", "W8"]
            selected_cam = st.radio("Select Camera Zone", wings)
            
        with c2:
            st.markdown(f"##### Viewer: Zone {selected_cam}")
            now_str = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
            
            cctv_html = f"""
            <div class='cctv-container'>
                <div class='cctv-live-badge'><div class='cctv-live-dot'></div> LIVE</div>
                <div class='cctv-timestamp'>{now_str}</div>
                <div class='cctv-center-text'>
                    <h1 style='color: #475569; margin-bottom: 0;'>📹</h1>
                    <h3>Live AI Processing Feed</h3>
                    <p>Camera: Zone {selected_cam} | YOLOv5n Active</p>
                    <small><i>(Note: In a production environment, this window connects to the edge RTSP stream)</i></small>
                </div>
                <div style='background: rgba(0,0,0,0.5); padding: 5px 10px; border-radius: 4px; color: white; width: fit-content; font-size: 12px;'>
                    Zone {selected_cam} - Main Aisle
                </div>
            </div>
            """
            st.markdown(cctv_html, unsafe_allow_html=True)

# --- 6. PAGE: SETTINGS & MANAGEMENT ---
elif menu_selection == "⚙️ Settings & Configuration":
    st.markdown("<div class='admin-header'><h2 style='margin:0;'>Settings & Configuration</h2><p style='margin:0; opacity: 0.8;'>Manage parking fees and facility layout information</p></div>", unsafe_allow_html=True)
    
    # FETCH CURRENT FEES FROM CLOUD (Using parking_fee table)
    try:
        settings_res = supabase.table("parking_fee").select("*").eq("id", 1).execute()
        current_settings = settings_res.data[0] if settings_res.data else {"base_fee": 2.0, "rate_per_second": 0.1}
    except:
        current_settings = {"base_fee": 2.0, "rate_per_second": 0.1}

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-title'>💳 Parking Fee Structure (Demo Mode)</div>", unsafe_allow_html=True)
        st.caption("Fees are synced to the cloud and update the live user dashboard instantly.")
        
        base_fee = st.number_input("Base Rate (RM per entry)", value=float(current_settings['base_fee']), step=0.50)
        sec_fee = st.number_input("Rate per Second Parked (RM)", value=float(current_settings['rate_per_second']), step=0.05)
        
        if st.button("💾 Save Fee Structure", key="save_fees"):
            try:
                # PUSH NEW FEES TO CLOUD
                supabase.table("parking_fee").upsert({"id": 1, "base_fee": base_fee, "rate_per_second": sec_fee}).execute()
                st.success("Fee structure successfully updated to Cloud Database!")
            except Exception as e:
                st.error("Failed to save. Please check your Supabase connection.")
            
        st.markdown(f"""
        <div style='background: #faf5ff; padding: 15px; border-radius: 8px; margin-top: 20px; border: 1px solid #e9d5ff;'>
            <strong>Fee Preview (Simulated)</strong><br>
            <span style='color: #6b7280; font-size: 14px;'>A car parked for 30 seconds will cost: </span> 
            <span style='float:right; font-weight:bold;'>RM {base_fee + (30 * sec_fee):.2f}</span><br>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-title'>📍 Facility Information</div>", unsafe_allow_html=True)
        
        f_name = st.text_input("Facility Name", value="Smart Parking Center")
        f_address = st.text_input("Address", value="123 Main Street, City Center")
        f_levels = st.text_input("Total Levels", value="5")
        f_hours = st.text_input("Operating Hours", value="24/7")
        
        if st.button("💾 Save Facility Info", key="save_fac"):
            st.success("Facility information updated in system.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. PAGE: GENERATE REPORTS ---
elif menu_selection == "📊 Generate Reports":
    st.markdown("<div class='admin-header'><h2 style='margin:0;'>Generate Reports</h2><p style='margin:0; opacity: 0.8;'>Analyze parking data, usage, and revenue</p></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='settings-card' style='margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown("##### 📅 Select Report Period")
    
    c1, c2 = st.columns(2)
    with c1: start_date = st.date_input("Start Date", value=date.today())
    with c2: end_date = st.date_input("End Date", value=date.today())
    
    if st.button("📈 Generate Financial & Usage Report"):
        with st.spinner("Querying Supabase database..."):
            df_history = get_cloud_data("transactions")
            
            if df_history.empty:
                st.warning("No transaction data found in the database yet.")
            else:
                # Convert string dates to datetime objects for filtering
                df_history['entry_time'] = pd.to_datetime(df_history['entry_time'])
                
                # Filter data based on selected dates
                mask = (df_history['entry_time'].dt.date >= start_date) & (df_history['entry_time'].dt.date <= end_date)
                filtered_df = df_history.loc[mask]
                
                if filtered_df.empty:
                    st.info(f"No parking sessions found between {start_date} and {end_date}.")
                else:
                    total_cars = len(filtered_df)
                    total_revenue = filtered_df['amount'].sum()
                    avg_stay = "2h 15m" # Simulated for display
                    
                    st.markdown("---")
                    st.markdown("### 📑 Report Summary")
                    
                    rc1, rc2, rc3 = st.columns(3)
                    rc1.metric("Total Cars Parked", total_cars)
                    rc2.metric("Total Revenue Generated", f"RM {total_revenue:.2f}")
                    rc3.metric("Average Stay Duration", avg_stay)
                    
                    st.markdown("#### 📝 Transaction Log")
                    # Clean up the dataframe for the admin table
                    display_df = filtered_df[['wing_id', 'slot_id', 'entry_time', 'exit_time', 'amount', 'payment_status']].sort_values(by='entry_time', ascending=False)
                    display_df.columns = ['Level', 'Slot', 'Entry Time', 'Exit Time', 'Fee (RM)', 'Status']
                    st.dataframe(display_df, use_container_width=True)
                    
    st.markdown("</div>", unsafe_allow_html=True)
