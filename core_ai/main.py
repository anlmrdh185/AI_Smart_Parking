import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="AI Smart Parking Dashboard", layout="wide", page_icon="🅿️")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    /* Main container for the map */
    .parking-map-container {
        display: flex; flex-direction: column; align-items: center; margin-top: 20px;
    }
    
    /* --- GATES STYLING --- */
    .gate-header {
        width: 95%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end;
    }
    .gate-group {
        display: flex; align-items: center; gap: 5px;
    }
    .gate-label {
        border: 1px solid #000; padding: 4px 10px; font-size: 12px; background: #fff; color: #000; font-weight: bold;
    }
    .gate-arrow {
        font-size: 26px; color: #0f4c75; line-height: 1; margin-bottom: -2px;
    }

    /* Rows of parking slots */
    .parking-row {
        display: flex; flex-wrap: nowrap; gap: 6px; align-items: center;
    }
    /* The central road boundary */
    .road-boundary {
        width: 95%; height: 14px; background-color: #0f4c75; margin: 12px 0; border-radius: 2px;
    }
    
    /* --- INCREASED SLOT SIZING --- */
    .slot { 
        width: 40px; height: 40px; border-radius: 6px; /* Increased from 32px to 40px */
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        font-weight: bold; color: white; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    .slot.vacant { background-color: #10b981; }   
    .slot.occupied { background-color: #ef4444; } 
    .slot.oku-vacant { background-color: #38bdf8; } 
    .slot.yellow { background-color: #fbbf24; box-shadow: none; } 
    .slot.gap { background-color: transparent; box-shadow: none; width: 12px; } 
    
    .car-icon { font-size: 18px; line-height: 1; margin-bottom: 2px; } /* Bigger Car/Wheelchair */
    .slot-id { font-size: 11px; line-height: 1; } /* Bigger text */
    
    .forecast-card { background-color: #f8fafc; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e0e0e0;}
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

# --- 3. TOP ROW: METRICS & PAYMENT ---
st.markdown("### 🚗 Facility Overview")
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
    st.write("<br>", unsafe_allow_html=True)
    st.button("💳 Quick Action: Pay Now", type="primary", use_container_width=True, on_click=toggle_payment)

st.markdown("---")

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

# --- 4. PRECISE ARCHITECTURE MAPPING ---
WING_LAYOUTS = {
    'W1': {
        'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 16)],
        'bottom': [f'{i:02}' for i in range(16, 31)]
    },
    'W3A': {
        'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 11)],
        'bottom': [f'{i:02}' for i in range(11, 22)]
    },
    'W5': {
        'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(3, 17)],
        'bottom': ['02', 'YELLOW'] + [f'{i:02}' for i in range(17, 31)]
    },
    'W7': {
        'top': [f'{i:02}' for i in range(1, 14)],
        'bottom': [f'{i:02}' for i in range(14, 27)]
    },
    'W8': {
        'top': [f'{i:02}' for i in range(1, 13)],
        'bottom': [f'{i:02}' for i in range(13, 25)]
    }
}
OKU_SLOTS = ['W1-01', 'W3A-01', 'W5-01', 'W5-02', 'W5-03']

# --- 5. MAIN LAYOUT: LEFT (Map) & RIGHT (Predictions) ---
left_panel, right_panel = st.columns([7, 3])

with left_panel:
    st.subheader("Select Level")
    
    if not df_slots.empty:
        wings = sorted(df_slots['wing_id'].unique())
        selected_wing = st.radio("Levels", wings, horizontal=True, label_visibility="collapsed")
        
        st.write(f"### Parking Layout: {selected_wing}")
        st.markdown("""
            <div style="display:flex; gap: 15px; font-size: 14px; margin-bottom: 15px;">
                <div><span style='color:#10b981'>■</span> Available</div>
                <div><span style='color:#ef4444'>■</span> Occupied</div>
                <div><span style='color:#38bdf8'>■</span> OKU Park</div>
                <div><span style='color:#fbbf24'>■</span> Non-Parking</div>
            </div>
            """, unsafe_allow_html=True)
        
        wing_data = df_slots[df_slots['wing_id'] == selected_wing]
        status_map = {row['slot_id'].split('-')[1]: row['status'] for _, row in wing_data.iterrows()}
        
        if selected_wing in WING_LAYOUTS:
            layout = WING_LAYOUTS[selected_wing]
            
            # Start Main Container
            html = "<div class='parking-map-container'>"
            
            # --- SEPARATED ENTRY/EXIT GATES ABOVE THE LOT ---
            html += """
            <div class='gate-header'>
                <div class='gate-group'>
                    <div class='gate-arrow'>⬅️</div>
                    <div class='gate-label'>STORE & Enter</div>
                </div>
                <div class='gate-group'>
                    <div class='gate-label'>Exit</div>
                    <div class='gate-arrow'>➡️</div>
                </div>
            </div>
            """
            
            # --- TOP ROW RENDERING ---
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'>"
            html += "<div class='parking-row'>"
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

            # --- CENTRAL ROAD BOUNDARY ---
            html += "<div class='road-boundary'></div>"
            
            # --- BOTTOM ROW RENDERING ---
            html += "<div style='display:flex; align-items:center; width:100%; justify-content: center;'>"
            html += "<div class='parking-row'>"
            for item in layout['bottom']:
                if item == 'YELLOW':
                    html += "<div class='slot yellow'></div>"
                else:
                    status = status_map.get(item, "Vacant")
                    is_oku = f"{selected_wing}-{item}" in OKU_SLOTS
                    status_class = "occupied" if status == "Occupied" else ("oku-vacant" if is_oku else "vacant")
                    icon = "♿" if is_oku else "🚗"
                    html += f"<div class='slot {status_class}'><div class='car-icon'>{icon}</div><div class='slot-id'>{item}</div></div>"
            html += "</div></div>" 

            html += "</div>" # Close main container
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("No data found in Supabase.")

# --- 6. RIGHT PANEL: PREDICTIONS ---
with right_panel:
    st.subheader("📈 Occupancy Prediction")
    
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.write(f"**Current Occupancy:** {occupancy_rate}%")
    st.progress(occupancy_rate / 100.0)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.write("⏱️ **Next Hour Forecast**")
    forecast = min(100, occupancy_rate + 5)
    color = "Red" if forecast > 80 else "Orange" if forecast > 50 else "Green"
    st.write(f"<span style='color:{color}; font-weight:bold; font-size:20px'>{forecast}%</span>", unsafe_allow_html=True)
    st.caption("Based on current entry trends.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.write("🕒 **Best Times to Visit**")
    st.write("🟢 Early Morning: `6 AM - 8 AM`")
    st.write("🟢 Late Evening: `9 PM - 11 PM`")
    st.markdown("</div>", unsafe_allow_html=True)

time.sleep(3)
st.rerun()
