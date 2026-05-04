import streamlit as st
import pandas as pd
import time
from datetime import datetime, date, time as dt_time
from supabase import create_client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="Smart Parking Admin", layout="wide", page_icon="🔐")

TABLE_MAP = {
    "Queensbay Mall": "Queensbay_Parking",
    "USM Mosque": "UsmMosque_Parking"
}

FACILITY_ID_MAP = {
    "Queensbay Mall": 1,
    "USM Mosque": 2
}

st.markdown("""
    <style>
    /* ADDED: Main Header & Logo Styling */
    .main-header {
        display: flex;
        align-items: center;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #3b82f6;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* UPDATED: NEW LOGO STYLE - Using P emoji inside a blue box */
    .logo-box {
        width: 60px;
        height: 60px;
        background-color: #3b82f6; /* Blue background to match design */
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        color: white;
        font-size: 40px; /* Large built-in icon */
        font-weight: bold;
        line-height: 1;
    }

    .metric-container { 
        background-color: #ffffff; 
        border: 1px solid #cbd5e1; /* Adds the box border */
        padding: 15px 20px; 
        border-radius: 12px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
    }
    <style>
    .stApp { background-color: #f8fafc; }
    .login-box { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #8b5cf6; }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-val { font-size: 28px; font-weight: bold; color: #1e293b; margin-top: 5px; }
    .metric-label { font-size: 13px; color: #64748b; font-weight: 500;}
    .sparkline { font-size: 20px; font-weight: bold; }
    .admin-header { background-color: #8b5cf6; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(139, 92, 246, 0.2); }
    .stButton>button { background-color: #8b5cf6; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: bold; width: 100%; transition: all 0.3s;}
    .stButton>button:hover { background-color: #7c3aed; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }
    
    /* CCTV Stream View - HEIGHT REDUCED TO 350px */
    .cctv-container { background-color: #0f172a; border-radius: 12px; padding: 20px; height: 350px; display: flex; flex-direction: column; justify-content: space-between; position: relative; border: 1px solid #334155;}
    .cctv-live-badge { position: absolute; top: 15px; right: 20px; color: #ef4444; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 5px;}
    .cctv-live-dot { width: 8px; height: 8px; background-color: #ef4444; border-radius: 50%; animation: pulse 1.5s infinite; }
    .cctv-timestamp { color: #94a3b8; font-size: 12px; font-family: monospace; }
    .cctv-center-text { text-align: center; color: #64748b; margin-top: 80px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
    
    /* FORCE VIDEO TO BE COMPACT AND FIT IN */
    video {
        max-height: 350px !important;
        border-radius: 12px !important;
        background-color: #0f172a;
    }

    .settings-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .settings-title { display: flex; align-items: center; gap: 10px; color: #1e293b; font-weight: bold; font-size: 18px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;}
    
    /* GRID CSS */
    .parking-map-container { display: flex; flex-direction: column; align-items: center; margin-top: 10px; }
    .gate-header { width: 95%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end; }
    .gate-group { display: flex; align-items: center; gap: 5px; }
    .gate-label { border: 1px solid #000; padding: 4px 10px; font-size: 12px; background: #fff; color: #000; font-weight: bold; }
    .gate-arrow { font-size: 26px; color: #0f4c75; line-height: 1; margin-bottom: -2px; }
    .parking-row { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center;}
    .road-boundary { width: 95%; height: 14px; background-color: #0f4c75; margin: 12px 0; border-radius: 2px; }
    .slot { width: 35px; height: 35px; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .slot.vacant { background-color: #10b981; } .slot.occupied { background-color: #ef4444; } .slot.oku-vacant { background-color: #38bdf8; } .slot.yellow { background-color: #fbbf24; box-shadow: none; } .slot.gap { background-color: transparent; box-shadow: none; width: 12px; }
    .car-icon { font-size: 16px; margin-bottom: 2px; line-height: 1; } .slot-id { font-size: 9px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION (FIXED CACHING!) ---
@st.cache_resource
def init_connection():
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Missing Streamlit Secrets. Please configure Supabase URL and Key.")
    st.stop()

def get_cloud_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()
        
# --- 3. AUTHENTICATION & MEMORY LOGIC ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if 'wing_videos' not in st.session_state:
    st.session_state.wing_videos = {}

if not st.session_state.admin_logged_in:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1e293b; margin-bottom: 5px;'>Admin Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-bottom: 20px;'>Sign in to manage the facility</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username", placeholder="Enter admin username")
    password = st.text_input("Password", type="password", placeholder="Enter password")
    
    if st.button("Secure Login"):
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
    
    st.markdown("""
        <div class="main-header">
            <img src="https://cdn-icons-png.flaticon.com/512/2764/2764359.png" width="60" style="margin-right: 20px;">
            <div>
                <h1 style="margin: 0; color: #1e293b; font-size: 32px;">AI Smart Parking Admin</h1>
                <p style="margin: 0; color: #64748b; font-size: 16px;">Live Facility Monitoring</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    facility = st.selectbox("Select Facility", list(TABLE_MAP.keys()))
    table_name = TABLE_MAP[facility]
    df = get_cloud_data(table_name)

    if df.empty:
        st.warning("No data found")
        st.stop()
    
    total = len(df)
    occupied = len(df[df['status'] == 'Occupied']) if not df.empty else 0
    available = total - occupied
    occ_rate = int((occupied / total) * 100) if total > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-container'><div><div class='metric-label'>Total Spaces</div><div class='metric-val'>{total}</div></div><div class='sparkline' style='color:#3b82f6;'>∿</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-container'><div><div class='metric-label'>Available</div><div class='metric-val'>{available}</div></div><div class='sparkline' style='color:#10b981;'>∿</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-container'><div><div class='metric-label'>Occupied</div><div class='metric-val'>{occupied}</div></div><div class='sparkline' style='color:#ef4444;'>∿</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-container'><div><div class='metric-label'>Occupancy</div><div class='metric-val'>{occ_rate}%</div></div><div class='sparkline' style='color:#8b5cf6;'>∿</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br><p style='color:#64748b; font-size:14px; margin-bottom: 5px;'>View Mode</p>", unsafe_allow_html=True)
    view_mode = st.radio("View Mode", ["Grid View", "CCTV Stream View"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    WING_LAYOUTS = {
        'W1': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 16)], 'bottom': [f'{i:02}' for i in range(16, 31)]},
        'W3A': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 11)], 'bottom': [f'{i:02}' for i in range(11, 22)]},
        'W5': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(3, 17)], 'bottom': ['02', 'YELLOW'] + [f'{i:02}' for i in range(17, 31)]},
        'W7': {'top': [f'{i:02}' for i in range(1, 14)], 'bottom': [f'{i:02}' for i in range(14, 27)]},
        'W8': {'top': [f'{i:02}' for i in range(1, 13)], 'bottom': [f'{i:02}' for i in range(13, 25)]},
        'M10': {'top': [f'{i:02}' for i in range(1,6)], 'bottom': [f'{i:02}' for i in range(6,13)]}
    }
    OKU_SLOTS = ['W1-01', 'W3A-01', 'W5-01', 'W5-02', 'W5-03']

    # --- GRID VIEW ---
    if view_mode == "Grid View":
        st.markdown("#### Live Parking Status")
        st.markdown("<span style='color:#10b981'>■ Available</span> &nbsp; <span style='color:#ef4444'>■ Occupied</span> &nbsp; <span style='color:#38bdf8'>■ OKU</span>", unsafe_allow_html=True)
        
        wings = sorted(df['wing_id'].unique()) if not df.empty else []
        selected_wing = st.selectbox("Select Level to Monitor", wings)
        
        if selected_wing in WING_LAYOUTS:
            st.write(f"**Level: {selected_wing}**")
            wing_data = df[df['wing_id'] == selected_wing]
            status_map = {}
            for _, row in wing_data.iterrows():
                if row.get("slot_id"):
                    parts = row["slot_id"].split("-")
                    if len(parts) == 2:
                        status_map[parts[1]] = row["status"]
            layout = WING_LAYOUTS[selected_wing]
            
            html = "<div style='background: white; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px;'>"
            html += "<div class='parking-map-container'>"
            
            html += """
            <div class='gate-header'>
                <div class='gate-group'><div class='gate-arrow'>⬅️</div><div class='gate-label'>STORE & Enter</div></div>
                <div class='gate-group'><div class='gate-label'>Exit</div><div class='gate-arrow'>➡️</div></div>
            </div>
            """
            
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'><div class='parking-row'>"
            for item in layout['top']:
                if item == 'YELLOW':
                    html += "<div class='slot yellow'></div>"
                else:
                    status = status_map.get(item, "Vacant")
                    is_oku = f"{selected_wing}-{item}" in OKU_SLOTS
                    status_class = "occupied" if status == "Occupied" else ("oku-vacant" if is_oku else "vacant")
                    icon = "♿" if is_oku else "🚗"
                    html += f"<div class='slot {status_class}'><div class='car-icon'>{icon}</div><div class='slot-id'>{item}</div></div>"
            html += "</div></div>" 

            html += "<div class='road-boundary'></div>"
            
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'><div class='parking-row'>"
            for item in layout['bottom']:
                if item == 'YELLOW':
                    html += "<div class='slot yellow'></div>"
                else:
                    status = status_map.get(item, "Vacant")
                    is_oku = f"{selected_wing}-{item}" in OKU_SLOTS
                    status_class = "occupied" if status == "Occupied" else ("oku-vacant" if is_oku else "vacant")
                    icon = "♿" if is_oku else "🚗"
                    html += f"<div class='slot {status_class}'><div class='car-icon'>{icon}</div><div class='slot-id'>{item}</div></div>"
            html += "</div></div></div></div>" 
            st.markdown(html, unsafe_allow_html=True)
            
            
    # --- CCTV STREAM VIEW ---
    elif view_mode == "CCTV Stream View":
        c1, c2 = st.columns([3, 7])
        with c1:
            st.markdown("##### Camera Feeds")
            wings = sorted(df['wing_id'].unique()) if not df.empty else ["W1", "W3A", "W5", "W7", "W8"]
            
            selected_cam = st.radio("Select Camera Zone", wings)
            st.markdown("---")
            
            st.markdown(f"**Upload Feed for {selected_cam}:**")
            uploaded_video = st.file_uploader("", type=['mp4', 'mov', 'avi'], key=f"uploader_{selected_cam}", label_visibility="collapsed")
            
            if uploaded_video is not None:
                st.session_state.wing_videos[selected_cam] = uploaded_video.read()
                st.success(f"Video saved for {selected_cam}!")
                
            if st.button("🗑️ Clear all stored videos"):
                st.session_state.wing_videos = {}
                st.rerun()
            
        with c2:
            st.markdown(f"##### Viewer: Zone {selected_cam}")
            
            if selected_cam in st.session_state.wing_videos:
                st.video(st.session_state.wing_videos[selected_cam])
            else:
                now_str = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
                cctv_html = f"""
                <div class='cctv-container'>
                    <div class='cctv-live-badge'><div class='cctv-live-dot'></div> WAITING</div>
                    <div class='cctv-timestamp'>{now_str}</div>
                    <div class='cctv-center-text'>
                        <h1 style='color: #475569; margin-bottom: 0;'>📹</h1>
                        <h3>No Feed Detected</h3>
                        <p>Camera: Zone {selected_cam}</p>
                        <small><i>Please upload a demo video using the sidebar to the left.</i></small>
                    </div>
                </div>
                """
                st.markdown(cctv_html, unsafe_allow_html=True)
                

# --- 6. PAGE: SETTINGS & MANAGEMENT ---
elif menu_selection == "⚙️ Settings & Configuration":
    st.markdown("<div class='admin-header'><h2 style='margin:0;'>Settings & Configuration</h2><p style='margin:0; opacity: 0.8;'>Manage parking fees and facility layout information</p></div>", unsafe_allow_html=True)
    # ADD THIS PICKER HERE:
    manage_place = st.selectbox("Select Facility to Configure", ["Queensbay Mall", "USM Mosque"])

    facility_id = FACILITY_ID_MAP[manage_place]
    table_name = TABLE_MAP[manage_place]   # also fix for manual update

    try:
        settings_res = supabase.table("parking_fee").select("*").eq("id", facility_id).execute()
        current_settings = settings_res.data[0] if settings_res.data else {"base_fee": 2.0, "rate_per_second": 0.1}
    except:
        current_settings = {"base_fee": 2.0, "rate_per_second": 0.1}

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💳 Parking Fee Structure")

        base_fee = st.number_input("Base Rate", value=float(current_settings['base_fee']))
        sec_fee = st.number_input("Rate per Second", value=float(current_settings['rate_per_second']))

        if st.button("💾 Save Fee Structure"):
            try:
                supabase.table("parking_fee").upsert({
                    "id": facility_id,
                    "base_fee": base_fee,
                    "rate_per_second": sec_fee,
                    "facility_name": manage_place
                }).execute()

                st.success(f"{manage_place} fees updated ✅")

            except Exception as e:
                st.error(f"Error: {e}")

            st.markdown(f"""
                <div style='background: #faf5ff; padding: 15px; border-radius: 8px; margin-top: 20px; border: 1px solid #e9d5ff;'>
                    <strong>Fee Preview </strong><br>
                    <span style='color: #6b7280; font-size: 14px;'>A car parked for 30 seconds will cost: </span> 
                    <span style='float:right; font-weight:bold;'>RM {base_fee + (30 * sec_fee):.2f}</span><br>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- RIGHT: FACILITY INFO ---
    with col2:
        st.markdown("### 📍 Facility Info")

        try:
            res = supabase.table("facility_info").select("*").eq("facility_name", manage_place).execute()
            info = res.data[0] if res.data else {}
        except:
            info = {}

        # --- INPUTS (DYNAMIC) ---
        f_name = st.text_input("Facility Name", value=info.get("facility_name", manage_place))
        f_address = st.text_input("Address", value=info.get("address", ""))
        f_levels = st.text_input("Total Levels", value=info.get("total_levels", ""))
        f_hours = st.text_input("Operating Hours", value=info.get("operating_hours", "24/7"))

        if st.button("💾 Save Facility Info"):
            supabase.table("facility_info").upsert({
            "facility_name": manage_place,
            "address": f_address,
            "total_levels": f_levels,
            "operating_hours": f_hours
        }).execute()

        st.success(f"{manage_place} updated ✅")

    # --- MANUAL SLOT UPDATE ---
    st.markdown("---")
    st.subheader("🔧 Manual Slot Update")

    slot_id = st.text_input("Slot ID")
    new_status = st.selectbox("Status", ["Vacant", "Occupied"])

    if st.button("Update Slot"):
        res = supabase.table(table_name).update({"status": new_status}).eq("slot_id", slot_id).execute()

        if res.data:
            st.success("Updated ✅")
        else:
            st.error("Slot not found")


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
                df_history['entry_time'] = pd.to_datetime(df_history['entry_time'])
                mask = (df_history['entry_time'].dt.date >= start_date) & (df_history['entry_time'].dt.date <= end_date)
                filtered_df = df_history.loc[mask]
                
                if filtered_df.empty:
                    st.info(f"No parking sessions found between {start_date} and {end_date}.")
                else:
                    total_cars = len(filtered_df)
                    total_revenue = filtered_df['amount'].sum()
                    avg_stay = "2h 15m"
                    
                    st.markdown("---")
                    st.markdown("### 📑 Report Summary")
                    
                    rc1, rc2, rc3 = st.columns(3)
                    rc1.metric("Total Cars Parked", total_cars)
                    rc2.metric("Total Revenue Generated", f"RM {total_revenue:.2f}")
                    rc3.metric("Average Stay Duration", avg_stay)
                    
                    st.markdown("#### 📝 Transaction Log")
                    display_df = filtered_df[['wing_id', 'slot_id', 'entry_time', 'exit_time', 'amount', 'payment_status']].sort_values(by='entry_time', ascending=False)
                    display_df.columns = ['Level', 'Slot', 'Entry Time', 'Exit Time', 'Fee (RM)', 'Status']
                    st.dataframe(display_df, use_container_width=True)
                    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- NEW: Auto-refresh ONLY when looking at the Grid! ---
    time.sleep(3)
    st.rerun()
