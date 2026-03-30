import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="AI Smart Parking Dashboard", layout="wide", page_icon="🅿️")
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
        background-color: #3b82f6; /* Blue background */
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
    
    /* --- NEW PAYMENT CARD STYLING --- */
    .payment-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    .payment-header { font-size: 20px; font-weight: 800; margin-bottom: 20px; color: #1e293b; text-align: center; letter-spacing: -0.5px;}
    .payment-divider { height: 2px; background: linear-gradient(to right, transparent, #e2e8f0, transparent); margin: 15px 0; }
    .payment-row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 15px; color: #64748b; align-items: center;}
    .payment-val { font-weight: 700; color: #1e293b; font-size: 16px; }
    .demo-badge { background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;}
    .payment-total-row { margin-top: 25px; background-color: #f8fafc; padding: 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border: 2px solid #8b5cf6;}
    .payment-total-label { font-size: 18px; font-weight: bold; color: #475569; }
    .payment-total-amount { font-size: 32px; font-weight: 900; color: #8b5cf6; line-height: 1;}
    
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

    /* NEW: Stretch the primary button to match metric box height perfectly */
    button[kind="primary"] {
        height: 88px; /* Matches the approximate height of your metric boxes */
        border-radius: 12px;
        font-size: 16px;
        font-weight: 700;
        margin-top: 1px; /* Tiny tweak to align the tops perfectly */
    }
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
st.markdown("""
    <div class="main-header">
        <div class="logo-box">🅿️</div>
        <div class="header-text">
            <h1 style="margin:0; color:#1e293b;">AI Smart Parking Dashboard</h1>
            <p style="margin:0; color:#64748b;">Live User Portal & Payments</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    st.button("💳 Quick Action: Pay Now", type="primary", use_container_width=True, on_click=toggle_payment)

st.markdown("---")

if 'payment_stage' not in st.session_state:
    st.session_state.payment_stage = "summary" # summary -> qr -> success

if st.session_state.show_payment:
    st.markdown("---")
    st.info("💳 **Secure Payment Portal**")
    
    # Step 1: Single Entry for Slot ID
    # We use session_state to "lock" the ID once entered so it doesn't ask again
    if 'confirmed_slot' not in st.session_state:
        st.session_state.confirmed_slot = None

    if st.session_state.payment_stage == "summary":
        entered_slot = st.text_input("Enter Your Parking Slot ID:", placeholder="e.g. W1-05").strip().upper()
        if entered_slot:
            st.session_state.confirmed_slot = entered_slot
    else:
        # Displays the slot ID as a header in Step 2 and 3 so user knows which one they are paying for
        st.markdown(f"### 🅿️ Slot: {st.session_state.confirmed_slot}")
        entered_slot = st.session_state.confirmed_slot

    if entered_slot and entered_slot in df_slots['slot_id'].values:
        row = df_slots[df_slots['slot_id'] == entered_slot].iloc[0]

        # 3. Check if the car is actually parked there
        if row['status'] == 'Occupied':
            # --- DYNAMIC FEE CALCULATION ---
            try:
                entry_time_str = row['start_time'].replace('T', ' ').split('.')[0]
                entry_time_dt = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
            except:
                entry_time_dt = datetime.now()
                
            duration = datetime.now() - entry_time_dt
            seconds_parked = duration.seconds
            blocks_of_10s = seconds_parked // 10
            
            try:
                settings_res = supabase.table("parking_fee").select("*").eq("id", 1).execute()
                if settings_res.data:
                    base_fee = float(settings_res.data[0]['base_fee'])
                    rate_per_10_sec = float(settings_res.data[0]['rate_per_second']) 
                else:
                    base_fee, rate_per_10_sec = 2.00, 0.10
            except:
                base_fee, rate_per_10_sec = 2.00, 0.10
                
            fee = base_fee + (blocks_of_10s * rate_per_10_sec)
            stable_ticket_id = abs(hash(entered_slot)) % 90000 + 10000

            # --- PAYMENT STAGES (FIXED INDENTATION) ---
            if st.session_state.payment_stage == "summary":
                payment_html = f"""
                <div class='payment-card'>
                    <div class='payment-header'>🅿️ Parking Fee Summary</div>
                    <div class='payment-row'><span>Ticket ID</span><span class='payment-val'>#{stable_ticket_id}</span></div>
                    <div class='payment-divider'></div>
                    <div class='payment-row'><span>Slot Location</span><span class='payment-val' style='font-size: 20px;'>{entered_slot}</span></div>
                    <div class='payment-row'><span>Entry Time</span><span class='payment-val'>{entry_time_dt.strftime('%I:%M:%S %p')}</span></div>
                    <div class='payment-divider'></div>
                    <div class='payment-row' style='background:#fff1f2; padding: 5px;'>
                        <span><span class='demo-badge'>FYP DEMO</span> Duration</span>
                        <span class='payment-val' style='color:#be123c;'>{seconds_parked} Seconds</span>
                    </div>
                    <div class='payment-row'>
                        <span>Applied Rate</span>
                        <span class='payment-val'>Base RM{base_fee:.2f} + RM{rate_per_10_sec:.2f}/10s</span>
                    </div>
                    <div class='payment-total-row'>
                        <span class='payment-total-label'>Total Due</span>
                        <span class='payment-total-amount'>RM {fee:.2f}</span>
                    </div>
                </div>
                """
                st.markdown(payment_html, unsafe_allow_html=True)
                if st.button("💳 Proceed to QR Payment", type="primary", use_container_width=True):
                    st.session_state.payment_stage = "qr"
                    st.rerun()

            # --- COMBINED QR & SUCCESS ACTION ---
            elif st.session_state.payment_stage == "qr":
                if st.session_state.get('payment_complete', False):
                    st.balloons()
                    st.success(f"✅ Payment Successful for {entered_slot}!")
        
                    st.markdown(f"""
                        <div style='background-color: #f0fdf4; padding: 25px; border-radius: 15px; border: 2px solid #22c55e;'>
                            <h2 style='color: #166534; margin-top: 0;'>🎫 Exit Pass</h2>
                            <hr style='border: 0.5px solid #bbf7d0;'>
                            <p style='font-size: 18px;'><b>Status:</b> PAID</p>
                            <p style='font-size: 18px;'><b>Action:</b> Barrier opening. You may now exit.</p>
                            <p style='font-size: 18px; color: #be123c;'><b>Grace Period:</b> 15 Minutes</p>
                        </div>
                    """, unsafe_allow_html=True)

                    if st.button("Finish & Return to Dashboard", use_container_width=True):
                        st.session_state.show_payment = False
                        st.session_state.payment_stage = "summary"
                        st.session_state.payment_complete = False # Reset for next time
                        if 'confirmed_slot' in st.session_state:
                            del st.session_state.confirmed_slot
                        st.rerun()
                else:
                    # 2. Otherwise, show the QR Code
                    st.markdown(f"""
                        <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                            <h3 style="color: #1e293b;">Scan to Pay RM {fee:.2f}</h3>
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PAY-{entered_slot}" 
                            style="border: 5px solid #3b82f6; border-radius: 12px; margin-bottom: 20px;">
                        </div>
                        """, unsafe_allow_html=True)
        
                    if st.button("✅ I Have Completed Payment", type="primary", use_container_width=True):
                        # 1. Update Database
                        with st.spinner("Verifying Payment..."):
                            supabase.table("slots").update({"status": "Vacant", "start_time": None}).eq("slot_id", entered_slot).execute()
                            st.session_state.payment_complete = True 
                            st.rerun()
                       

                    if st.button("⬅️ Cancel Payment"):
                        st.session_state.payment_stage = "summary"
                        st.rerun()
        else:
            st.warning(f"✅ Slot **{entered_slot}** is currently vacant. No payment required.")
    elif entered_slot:
        st.error("❌ Invalid Slot ID. Please check the lot number (e.g., W1-05) and try again.")

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
                    <div class='gate-label'>STORE & MALL</div>
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

# --- 6. RIGHT PANEL: CUSTOM PREDICTION UI ---
with right_panel:
    st.markdown("#### 📈 Occupancy Prediction")
    
    # Logic for the dynamic Next Hour Forecast
    forecast = min(100, occupancy_rate + 5)
    if forecast < 50:
        badge_class = "badge-low"
        badge_text = "Low"
        sub_text = "Off-peak hours"
    elif forecast < 80:
        badge_class = "badge-med"
        badge_text = "Medium"
        sub_text = "Steady traffic"
    else:
        badge_class = "badge-high"
        badge_text = "High"
        sub_text = "Peak hours approaching"

    # FLATTENED HTML to prevent Streamlit from making it a code block
    pred_html = f"<div class='pred-card-blue'><div class='pred-header'><span>Current Occupancy</span><span class='pred-header-val'>{occupancy_rate}%</span></div><div class='progress-track'><div class='progress-fill-blue' style='width: {occupancy_rate}%;'></div></div></div>"
    
    pred_html += f"<div class='pred-card-purple'><div class='pred-header'><span>🕒 Next Hour Forecast</span><span class='forecast-val'>{forecast}%</span></div><span class='{badge_class}'>{badge_text}</span><div class='sub-text'>{sub_text}</div></div>"
    
    pred_html += "<div style='font-size: 13px; color: #059669; margin-bottom: 8px;'>① Best Times to Visit</div>"
    pred_html += "<div class='time-pill'><span style='color: #475569; font-weight: normal;'>Early Morning</span><span>6 AM - 8 AM</span></div>"
    pred_html += "<div class='time-pill'><span style='color: #475569; font-weight: normal;'>Late Evening</span><span>9 PM - 11 PM</span></div>"
    
    pred_html += "<div style='font-size: 13px; color: #475569; margin: 15px 0 10px 0;'>Today's Forecast</div>"
    
    # Mock data for the bar chart
    forecast_data = [
        ("8 AM", 75, "fill-orange"), ("10 AM", 82, "fill-orange"),
        ("12 PM", 95, "fill-red"), ("2 PM", 88, "fill-red"),
        ("4 PM", 78, "fill-orange"), ("6 PM", 90, "fill-red"),
        ("8 PM", 65, "fill-yellow"), ("10 PM", 45, "fill-green")
    ]
    
    # FLATTENED Loop
    for time_label, val, color_class in forecast_data:
        pred_html += f"<div class='bar-chart-row'><div class='bar-chart-time'>{time_label}</div><div class='bar-chart-track'><div class='bar-chart-fill {color_class}' style='width: {val}%;'></div></div><div class='bar-chart-val'>{val}%</div></div>"
        
    st.markdown(pred_html, unsafe_allow_html=True)

time.sleep(3)
st.rerun()
