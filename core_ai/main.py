import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="AI Smart Parking Dashboard", layout="wide", page_icon="🅿️")

st.markdown("""
    <style>
    /* ADDED: Header & Logo Styling */
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
    .logo-img { width: 60px; margin-right: 20px; }
    
    /* ADDED: Box styling for metrics */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }

    /* ADDED: Button Box to match Metric Height */
    .button-box {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        padding: 15px;
        border-radius: 12px;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Original CSS preserved */
    .parking-map-container { display: flex; flex-direction: column; align-items: center; margin-top: 20px; }
    .gate-header { width: 95%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end; }
    .gate-group { display: flex; align-items: center; gap: 5px; }
    .gate-label { border: 1px solid #000; padding: 4px 10px; font-size: 12px; background: #fff; color: #000; font-weight: bold; }
    .gate-arrow { font-size: 26px; color: #0f4c75; line-height: 1; margin-bottom: -2px; }
    .parking-row { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; }
    .road-boundary { width: 95%; height: 14px; background-color: #0f4c75; margin: 12px 0; border-radius: 2px; }
    .slot { width: 40px; height: 40px; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
    .slot.vacant { background-color: #10b981; }   
    .slot.occupied { background-color: #ef4444; } 
    .slot.oku-vacant { background-color: #38bdf8; } 
    .slot.yellow { background-color: #fbbf24; box-shadow: none; } 
    .car-icon { font-size: 18px; line-height: 1; margin-bottom: 2px; } 
    .slot-id { font-size: 11px; line-height: 1; } 
    .pred-card-blue { background-color: #eff6ff; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dbeafe; }
    .pred-card-purple { background-color: #faf5ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #f3e8ff; }
    .progress-track { width: 100%; background-color: #ffffff; border-radius: 4px; height: 8px; overflow: hidden; border: 1px solid #e2e8f0;}
    .progress-fill-blue { background-color: #2563eb; height: 100%; border-radius: 4px; }
    .time-pill { background-color: #ecfdf5; color: #059669; padding: 10px 15px; border-radius: 8px; display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; }
    .bar-chart-row { display: flex; align-items: center; font-size: 11px; margin-bottom: 8px; color: #475569;}
    .bar-chart-track { flex-grow: 1; background-color: #f1f5f9; height: 6px; border-radius: 3px; margin: 0 10px; overflow: hidden; }
    .bar-chart-fill { height: 100%; border-radius: 3px; }
    .fill-red { background-color: #ef4444; } .fill-orange { background-color: #f97316; } .fill-yellow { background-color: #eab308; } .fill-green { background-color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

def get_cloud_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

df_slots = get_cloud_data("slots")

if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

def toggle_payment():
    st.session_state.show_payment = not st.session_state.show_payment

# --- 3. UPDATED HEADER & METRICS ---
st.markdown("""
    <div class="main-header">
        <img src="https://cdn-icons-png.flaticon.com/512/2764/2764359.png" class="logo-img">
        <div class="header-text">
            <h1 style="margin:0; color:#1e293b;">AI Smart Parking Dashboard</h1>
            <p style="margin:0; color:#64748b;">Live User Portal & Payments</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if not df_slots.empty:
    total_spaces = len(df_slots)
    occupied_spaces = len(df_slots[df_slots['status'] == 'Occupied'])
    available_spaces = total_spaces - occupied_spaces
    occupancy_rate = int((occupied_spaces / total_spaces) * 100) if total_spaces > 0 else 0
else:
    total_spaces, available_spaces, occupancy_rate = 0, 0, 0

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
col1.metric("📍 Total Spaces", total_spaces)
col2.metric("🟢 Available", available_spaces)
col3.metric("📈 Occupancy Rate", f"{occupancy_rate}%")

with col4:
    st.markdown('<div class="button-box">', unsafe_allow_html=True)
    st.button("💳 Pay Now", type="primary", use_container_width=True, on_click=toggle_payment)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# [Rest of main.py remains exactly as your original file...]
if st.session_state.show_payment:
    st.info("💳 **Payment Portal**")
    if not df_slots.empty:
        occupied_df = df_slots[df_slots['status'] == 'Occupied']
        if occupied_df.empty:
            st.write("No cars are currently parked.")
        else:
            pc1, pc2 = st.columns(2)
            with pc1:
                selected_slot = st.selectbox("Select your Slot ID:", occupied_df['slot_id'])
            with pc2:
                row = occupied_df[occupied_df['slot_id'] == selected_slot].iloc[0]
                entry_time = datetime.strptime(row['start_time'].replace('T', ' ').split('.')[0], '%Y-%m-%d %H:%M:%S')
                duration = datetime.now() - entry_time
                hours = max(1, duration.seconds // 3600)
                fee = 2.00 + (max(0, hours - 1) * 1.00)
                
                st.write(f"**Parked Duration:** {hours} Hour(s)")
                st.write(f"**Amount Due:** RM {fee:.2f}")
                if st.button("Confirm Payment", type="primary"):
                    st.success("Payment successful! Please exit within 15 minutes.")
                    st.session_state.show_payment = False
    st.markdown("---")

WING_LAYOUTS = {
    'W1': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 16)], 'bottom': [f'{i:02}' for i in range(16, 31)]},
    'W3A': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 11)], 'bottom': [f'{i:02}' for i in range(11, 22)]},
    'W5': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(3, 17)], 'bottom': ['02', 'YELLOW'] + [f'{i:02}' for i in range(17, 31)]},
    'W7': {'top': [f'{i:02}' for i in range(1, 14)], 'bottom': [f'{i:02}' for i in range(14, 27)]},
    'W8': {'top': [f'{i:02}' for i in range(1, 13)], 'bottom': [f'{i:02}' for i in range(13, 25)]}
}
OKU_SLOTS = ['W1-01', 'W3A-01', 'W5-01', 'W5-02', 'W5-03']

left_panel, right_panel = st.columns([7, 3])

with left_panel:
    st.subheader("Select Level")
    if not df_slots.empty:
        wings = sorted(df_slots['wing_id'].unique())
        selected_wing = st.radio("Levels", wings, horizontal=True, label_visibility="collapsed")
        st.write(f"### Parking Layout: {selected_wing}")
        st.markdown("""<div style="display:flex; gap: 15px; font-size: 14px; margin-bottom: 15px;"><div><span style='color:#10b981'>■</span> Available</div><div><span style='color:#ef4444'>■</span> Occupied</div><div><span style='color:#38bdf8'>■</span> OKU Park</div><div><span style='color:#fbbf24'>■</span> Non-Parking</div></div>""", unsafe_allow_html=True)
        wing_data = df_slots[df_slots['wing_id'] == selected_wing]
        status_map = {row['slot_id'].split('-')[1]: row['status'] for _, row in wing_data.iterrows()}
        if selected_wing in WING_LAYOUTS:
            layout = WING_LAYOUTS[selected_wing]
            html = "<div class='parking-map-container'><div class='gate-header'><div class='gate-group'><div class='gate-arrow'>⬅️</div><div class='gate-label'>STORE & Enter</div></div><div class='gate-group'><div class='gate-label'>Exit</div><div class='gate-arrow'>➡️</div></div></div>"
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'><div class='parking-row'>"
            for item in layout['top']:
                if item == 'YELLOW': html += "<div class='slot yellow'></div>"
                else:
                    status = status_map.get(item, "Vacant")
                    is_oku = f"{selected_wing}-{item}" in OKU_SLOTS
                    status_class = "occupied" if status == "Occupied" else ("oku-vacant" if is_oku else "vacant")
                    icon = "♿" if is_oku else "🚗"
                    html += f"<div class='slot {status_class}'><div class='car-icon'>{icon}</div><div class='slot-id'>{item}</div></div>"
            html += "</div></div><div class='road-boundary'></div>"
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'><div class='parking-row'>"
            for item in layout['bottom']:
                if item == 'YELLOW': html += "<div class='slot yellow'></div>"
                else:
                    status = status_map.get(item, "Vacant")
                    is_oku = f"{selected_wing}-{item}" in OKU_SLOTS
                    status_class = "occupied" if status == "Occupied" else ("oku-vacant" if is_oku else "vacant")
                    icon = "♿" if is_oku else "🚗"
                    html += f"<div class='slot {status_class}'><div class='car-icon'>{icon}</div><div class='slot-id'>{item}</div></div>"
            html += "</div></div></div>" 
            st.markdown(html, unsafe_allow_html=True)

with right_panel:
    st.markdown("#### 📈 Occupancy Prediction")
    df_history = get_cloud_data("transactions")
    forecast = min(100, occupancy_rate + 5)
    pred_html = f"<div class='pred-card-blue'><span>Current Occupancy</span><span style='float:right;'>{occupancy_rate}%</span><div class='progress-track'><div class='progress-fill-blue' style='width: {occupancy_rate}%;'></div></div></div>"
    pred_html += f"<div class='pred-card-purple'><span>🕒 Next Hour Forecast</span><span style='float:right; font-weight:bold;'>{forecast}%</span></div>"
    st.markdown(pred_html, unsafe_allow_html=True)

time.sleep(3)
st.rerun()
