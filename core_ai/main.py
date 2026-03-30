import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION & CSS ---
st.set_page_config(page_title="AI Smart Parking Dashboard", layout="wide", page_icon="🅿️")

st.markdown("""
    <style>
    /* Main Header with Logo */
    .main-header {
        display: flex;
        align-items: center;
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #3b82f6; /* Blue border */
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .logo-img { width: 60px; margin-right: 20px; }
    .header-text h1 { margin: 0; color: #1e293b; font-size: 28px; }
    
    /* Structured Metric Boxes */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }

    /* Parking Grid Styling */
    .parking-grid { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; align-items: center;}
    .slot { 
        width: 50px; height: 50px; border-radius: 8px; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        font-weight: bold; color: white; font-size: 14px; box-shadow: 1px 1px 4px rgba(0,0,0,0.2);
    }
    .slot.occupied { background-color: #ef4444; } 
    .slot.vacant { background-color: #10b981; }   
    .car-icon { font-size: 18px; line-height: 1; margin-bottom: 2px; }
    .slot-id { font-size: 10px; line-height: 1; }
    .gate { background-color: #3b82f6; color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; font-size: 12px; }
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

# --- 3. HEADER & METRICS ---
st.markdown("""
    <div class="main-header">
        <img src="https://cdn-icons-png.flaticon.com/512/2764/2764359.png" class="logo-img">
        <div class="header-text">
            <h1>AI Smart Parking Dashboard</h1>
            <p style="margin:0; color:#64748b;">Live Facility Management & Predictions</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

df_slots = get_cloud_data("slots")

if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

def toggle_payment():
    st.session_state.show_payment = not st.session_state.show_payment

if not df_slots.empty:
    total_spaces = len(df_slots)
    occupied_spaces = len(df_slots[df_slots['status'] == 'Occupied'])
    available_spaces = total_spaces - occupied_spaces
    occupancy_rate = int((occupied_spaces / total_spaces) * 100) if total_spaces > 0 else 0
else:
    total_spaces, available_spaces, occupancy_rate = 0, 0, 0

m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
m1.metric("📍 Total Spaces", total_spaces)
m2.metric("🟢 Available", available_spaces)
m3.metric("📈 Occupancy Rate", f"{occupancy_rate}%")
with m4:
    st.write("<br>", unsafe_allow_html=True)
    st.button("💳 Quick Action: Pay Now", type="primary", use_container_width=True, on_click=toggle_payment)

st.markdown("---")

# --- 4. PAYMENT PORTAL & MAIN CONTENT ---
if st.session_state.show_payment:
    st.info("💳 **Payment Portal**")
    occupied_df = df_slots[df_slots['status'] == 'Occupied'] if not df_slots.empty else pd.DataFrame()
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

left_panel, right_panel = st.columns([7, 3])

with left_panel:
    st.subheader("Select Level")
    if not df_slots.empty:
        wings = sorted(df_slots['wing_id'].unique())
        selected_wing = st.radio("Levels", wings, horizontal=True, label_visibility="collapsed")
        st.write(f"### Parking Layout: {selected_wing}")
        st.markdown("<span style='color:#10b981'>🟢 Available</span> &nbsp;&nbsp; <span style='color:#ef4444'>🔴 Occupied</span>", unsafe_allow_html=True)
        wing_data = df_slots[df_slots['wing_id'] == selected_wing].sort_values(by='slot_id')
        
        html_grid = "<div class='parking-grid'><div class='gate'>IN ➡️</div>"
        for idx, row in wing_data.iterrows():
            status_class = "occupied" if row['status'] == "Occupied" else "vacant"
            slot_name = row['slot_id'].split('-')[1]
            html_grid += f"<div class='slot {status_class}'><div class='car-icon'>🚗</div><div class='slot-id'>{slot_name}</div></div>"
        html_grid += "<div class='gate'>➡️ OUT</div></div>"
        st.markdown(html_grid, unsafe_allow_html=True)
    else:
        st.warning("No data found.")

with right_panel:
    st.subheader("📈 Occupancy Prediction")
    st.markdown(f"<div class='forecast-card'>**Current Occupancy:** {occupancy_rate}%", unsafe_allow_html=True)
    st.progress(occupancy_rate / 100.0)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='forecast-card'>⏱️ **Next Hour Forecast**", unsafe_allow_html=True)
    forecast = min(100, occupancy_rate + 5)
    color = "Red" if forecast > 80 else "Orange" if forecast > 50 else "Green"
    st.write(f"<span style='color:{color}; font-weight:bold; font-size:20px'>{forecast}%</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

time.sleep(3)
st.rerun()
