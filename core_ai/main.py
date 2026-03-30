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
    .parking-map-container { display: flex; flex-direction: column; align-items: center; margin-top: 20px; }
    
    /* GATES STYLING */
    .gate-header { width: 95%; display: flex; justify-content: space-between; margin-bottom: 5px; align-items: flex-end; }
    .gate-group { display: flex; align-items: center; gap: 5px; }
    .gate-label { border: 1px solid #000; padding: 4px 10px; font-size: 12px; background: #fff; color: #000; font-weight: bold; }
    .gate-arrow { font-size: 26px; color: #0f4c75; line-height: 1; margin-bottom: -2px; }

    /* PARKING GRID STYLING */
    .parking-row { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; }
    .road-boundary { width: 95%; height: 14px; background-color: #0f4c75; margin: 12px 0; border-radius: 2px; }
    .slot { 
        width: 40px; height: 40px; border-radius: 6px; display: flex; flex-direction: column; 
        align-items: center; justify-content: center; font-weight: bold; color: white; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    .slot.vacant { background-color: #10b981; }   
    .slot.occupied { background-color: #ef4444; } 
    .slot.oku-vacant { background-color: #38bdf8; } 
    .slot.yellow { background-color: #fbbf24; box-shadow: none; } 
    .slot.gap { background-color: transparent; box-shadow: none; width: 12px; } 
    .car-icon { font-size: 18px; line-height: 1; margin-bottom: 2px; } 
    .slot-id { font-size: 11px; line-height: 1; } 
    
    /* --- NEW PREDICTION CENTER STYLING --- */
    .pred-card-blue { background-color: #eff6ff; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dbeafe; }
    .pred-card-purple { background-color: #faf5ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #f3e8ff; }
    .pred-header { display: flex; justify-content: space-between; font-size: 13px; color: #475569; margin-bottom: 8px; }
    .pred-header-val { font-weight: bold; color: #1e293b; font-size: 14px; }
    
    /* Progress Bars */
    .progress-track { width: 100%; background-color: #ffffff; border-radius: 4px; height: 8px; overflow: hidden; border: 1px solid #e2e8f0;}
    .progress-fill-blue { background-color: #2563eb; height: 100%; border-radius: 4px; }
    
    /* Badges & Text */
    .badge-low { background-color: #dcfce7; color: #166534; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;}
    .badge-high { background-color: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;}
    .badge-med { background-color: #fef9c3; color: #854d0e; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;}
    .forecast-val { font-size: 16px; font-weight: bold; color: #7e22ce; }
    .sub-text { font-size: 11px; color: #64748b; margin-top: 8px; }
    
    /* Best Times Pills */
    .time-pill { background-color: #ecfdf5; color: #059669; padding: 10px 15px; border-radius: 8px; display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; }
    
    /* Chart Rows */
    .bar-chart-row { display: flex; align-items: center; font-size: 11px; margin-bottom: 8px; color: #475569;}
    .bar-chart-time { width: 40px; font-weight: 500;}
    .bar-chart-track { flex-grow: 1; background-color: #f1f5f9; height: 6px; border-radius: 3px; margin: 0 10px; overflow: hidden; }
    .bar-chart-fill { height: 100%; border-radius: 3px; }
    .bar-chart-val { width: 30px; text-align: right; }
    .fill-red { background-color: #ef4444; }
    .fill-orange { background-color: #f97316; }
    .fill-yellow { background-color: #eab308; }
    .fill-green { background-color: #10b981; }
    </style>
    <style>
    /* 1. Main Header with Logo */
    .main-header {
        display: flex;
        align-items: center;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #8b5cf6; /* Purple border */
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .logo-img {
        width: 60px;
        margin-right: 20px;
    }
    .header-text h1 {
        margin: 0;
        color: #1e293b;
        font-size: 28px;
    }
    
    /* 2. Structured Metric Boxes */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #e2e8f0; /* Soft gray border */
        padding: 15px 20px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #8b5cf6;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
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
    'W1': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 16)], 'bottom': [f'{i:02}' for i in range(16, 31)]},
    'W3A': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(2, 11)], 'bottom': [f'{i:02}' for i in range(11, 22)]},
    'W5': {'top': ['01', 'YELLOW'] + [f'{i:02}' for i in range(3, 17)], 'bottom': ['02', 'YELLOW'] + [f'{i:02}' for i in range(17, 31)]},
    'W7': {'top': [f'{i:02}' for i in range(1, 14)], 'bottom': [f'{i:02}' for i in range(14, 27)]},
    'W8': {'top': [f'{i:02}' for i in range(1, 13)], 'bottom': [f'{i:02}' for i in range(13, 25)]}
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
            html = "<div class='parking-map-container'>"
            
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
            html += "</div></div></div>" 
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("No data found in Supabase.")

# --- 6. RIGHT PANEL: DATA-DRIVEN PREDICTION UI ---
with right_panel:
    st.markdown("#### 📈 Occupancy Prediction")
    
    # Fetch historical data for predictions
    df_history = get_cloud_data("transactions")
    
    # 1. Dynamic Next Hour Forecast Logic
    forecast = min(100, occupancy_rate + 5)
    if forecast < 50:
        badge_class, badge_text, sub_text = "badge-low", "Low", "Off-peak hours"
    elif forecast < 80:
        badge_class, badge_text, sub_text = "badge-med", "Medium", "Steady traffic"
    else:
        badge_class, badge_text, sub_text = "badge-high", "High", "Peak hours approaching"

    pred_html = f"<div class='pred-card-blue'><div class='pred-header'><span>Current Occupancy</span><span class='pred-header-val'>{occupancy_rate}%</span></div><div class='progress-track'><div class='progress-fill-blue' style='width: {occupancy_rate}%;'></div></div></div>"
    pred_html += f"<div class='pred-card-purple'><div class='pred-header'><span>🕒 Next Hour Forecast</span><span class='forecast-val'>{forecast}%</span></div><span class='{badge_class}'>{badge_text}</span><div class='sub-text'>{sub_text}</div></div>"
    
    # 2. DATA-DRIVEN ANALYTICS
    if not df_history.empty:
        # Convert times to pandas datetime
        df_history['entry_time'] = pd.to_datetime(df_history['entry_time'])
        df_history['hour'] = df_history['entry_time'].dt.hour
        
        # Count how many cars park during each hour historically
        hourly_traffic = df_history.groupby('hour').size()
        max_traffic = hourly_traffic.max() if not hourly_traffic.empty else 1
        
        # Find the two quietest hours (Best times to visit) between 6 AM and 10 PM
        day_hours = hourly_traffic[(hourly_traffic.index >= 6) & (hourly_traffic.index <= 22)]
        if not day_hours.empty:
            quietest_hours = day_hours.nsmallest(2).index.tolist()
        else:
            quietest_hours = [7, 21] # Fallback
            
        def format_hour(h):
            am_pm = "AM" if h < 12 else "PM"
            disp_h = h if h <= 12 else h - 12
            if disp_h == 0: disp_h = 12
            return f"{disp_h} {am_pm}"

        pred_html += "<div style='font-size: 13px; color: #059669; margin-bottom: 8px;'>① Best Times to Visit (Based on Data)</div>"
        
        for qh in quietest_hours:
            pred_html += f"<div class='time-pill'><span style='color: #475569; font-weight: normal;'>Recommended</span><span>{format_hour(qh)} - {format_hour(qh+2)}</span></div>"
        
        pred_html += "<div style='font-size: 13px; color: #475569; margin: 15px 0 10px 0;'>Today's Forecast (Historical Average)</div>"
        
        # Generate the bar chart for specific display hours
        display_hours = [8, 10, 12, 14, 16, 18, 20, 22]
        for h in display_hours:
            count = hourly_traffic.get(h, 0)
            # Normalize to a percentage (0-100%)
            percentage = int((count / max_traffic) * 100) if max_traffic > 0 else 0
            
            # Determine color dynamically
            if percentage >= 80: color_class = "fill-red"
            elif percentage >= 60: color_class = "fill-orange"
            elif percentage >= 40: color_class = "fill-yellow"
            else: color_class = "fill-green"
            
            pred_html += f"<div class='bar-chart-row'><div class='bar-chart-time'>{format_hour(h)}</div><div class='bar-chart-track'><div class='bar-chart-fill {color_class}' style='width: {percentage}%;'></div></div><div class='bar-chart-val'>{percentage}%</div></div>"

    else:
        pred_html += "<div style='font-size: 12px; color: red;'>No historical data available for forecast yet.</div>"

    st.markdown(pred_html, unsafe_allow_html=True)

time.sleep(3)
st.rerun()
