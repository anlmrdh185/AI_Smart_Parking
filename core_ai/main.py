import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="AI Smart Parking Dashboard", layout="wide", page_icon="🅿️")

# Custom CSS to mimic the modern UI in your design
st.markdown("""
    <style>
    /* Styling for the top metric cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    /* Styling for the parking grid */
    .parking-grid { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; align-items: center;}
    .slot { 
        width: 50px; height: 50px; border-radius: 8px; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        font-weight: bold; color: white; font-size: 14px; box-shadow: 1px 1px 4px rgba(0,0,0,0.2);
    }
    .slot.occupied { background-color: #ef4444; } /* Red */
    .slot.vacant { background-color: #10b981; }   /* Green */
    .car-icon { font-size: 18px; line-height: 1; margin-bottom: 2px; }
    .slot-id { font-size: 10px; line-height: 1; }
    
    /* Styling for the IN/OUT Gates */
    .gate {
        background-color: #3b82f6; color: white; padding: 10px 15px; 
        border-radius: 8px; font-weight: bold; font-size: 12px;
        display: flex; align-items: center; justify-content: center; text-align: center;
    }
    
    /* Styling for right panel cards */
    .forecast-card { background-color: #f8fafc; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e0e0e0;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

def get_cloud_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

# Fetch Live Data
df_slots = get_cloud_data("slots")

# State Management for Payment Portal
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

def toggle_payment():
    st.session_state.show_payment = not st.session_state.show_payment

# --- 3. TOP ROW: METRICS & PAYMENT BUTTON ---
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
    st.write("<br>", unsafe_allow_html=True) # Spacing alignment
    st.button("💳 Quick Action: Pay Now", type="primary", use_container_width=True, on_click=toggle_payment)

st.markdown("---")

# --- 4. CONDITIONAL PAYMENT PORTAL ---
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

# --- 5. MAIN LAYOUT: LEFT (Grid) & RIGHT (Predictions) ---
left_panel, right_panel = st.columns([7, 3])

# --- LEFT PANEL: PARKING ARRANGEMENT ---
with left_panel:
    st.subheader("Select Level")
    
    if not df_slots.empty:
        wings = sorted(df_slots['wing_id'].unique())
        # Use a horizontal radio button to mimic the level selector in your image
        selected_wing = st.radio("Levels", wings, horizontal=True, label_visibility="collapsed")
        
        st.write(f"### Parking Layout: {selected_wing}")
        st.markdown("<span style='color:#10b981'>🟢 Available</span> &nbsp;&nbsp; <span style='color:#ef4444'>🔴 Occupied</span>", unsafe_allow_html=True)
        
        wing_data = df_slots[df_slots['wing_id'] == selected_wing].sort_values(by='slot_id')
        
        # HTML construction for the parking grid
        html_grid = "<div class='parking-grid'>"
        
        # IN GATE
        html_grid += "<div class='gate'>IN ➡️</div>"
        
        for idx, row in wing_data.iterrows():
            status_class = "occupied" if row['status'] == "Occupied" else "vacant"
            slot_name = row['slot_id'].split('-')[1] # Just get the number (e.g., 01, 02)
            html_grid += f"""
                <div class='slot {status_class}'>
                    <div class='car-icon'>🚗</div>
                    <div class='slot-id'>{slot_name}</div>
                </div>
            """
            
        # OUT GATE
        html_grid += "<div class='gate'>➡️ OUT</div>"
        html_grid += "</div>"
        
        st.markdown(html_grid, unsafe_allow_html=True)
        
    else:
        st.warning("No data found in Supabase.")

# --- RIGHT PANEL: PREDICTIONS & ANALYTICS ---
with right_panel:
    st.subheader("📈 Occupancy Prediction")
    
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.write(f"**Current Occupancy:** {occupancy_rate}%")
    st.progress(occupancy_rate / 100.0)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='forecast-card'>", unsafe_allow_html=True)
    st.write("⏱️ **Next Hour Forecast**")
    # Simple logic to simulate a forecast
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

# Auto-Refresh every few seconds
time.sleep(3)
st.rerun()