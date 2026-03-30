import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Smart Parking", layout="wide", page_icon="🅿️")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e2e8f0;
        padding: 15px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .parking-grid { display: flex; flex-wrap: wrap; gap: 8px; margin: 15px 0; justify-content: center; }
    .slot { 
        width: 50px; height: 50px; border-radius: 8px; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        font-weight: bold; color: white; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
    }
    .slot.occupied { background-color: #ef4444; }
    .slot.vacant { background-color: #10b981; }
    .slot-id { font-size: 10px; }
    .payment-card {
        background: white; padding: 20px; border-radius: 15px;
        border: 2px solid #8b5cf6; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SUPABASE CONNECTION ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_cloud_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

# State Management
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False

# --- 3. DATA FETCHING ---
df_slots = get_cloud_data("slots")

# --- 4. TOP METRICS ---
st.title("🚗 Smart Parking User Portal")
if not df_slots.empty:
    total = len(df_slots)
    occupied = len(df_slots[df_slots['status'] == 'Occupied'])
    col1, col2, col3 = st.columns([1,1,1])
    col1.metric("📍 Total Spaces", total)
    col2.metric("🟢 Available", total - occupied)
    col3.button("💳 Pay Parking Fee", type="primary", use_container_width=True, on_click=lambda: setattr(st.session_state, 'show_payment', not st.session_state.show_payment))

# --- 5. PAYMENT PORTAL (Optimized) ---
if st.session_state.show_payment:
    st.markdown("<div class='payment-card'>", unsafe_allow_html=True)
    occupied_slots = df_slots[df_slots['status'] == 'Occupied']
    
    if occupied_slots.empty:
        st.warning("No occupied slots found to process payment.")
    else:
        entered_slot = st.selectbox("Select your Slot ID:", occupied_slots['slot_id'])
        row = occupied_slots[occupied_slots['slot_id'] == entered_slot].iloc[0]
        
        # Calculation Logic (Every 10 Seconds)
        entry_time_dt = datetime.strptime(row['start_time'].replace('T', ' ').split('.')[0], '%Y-%m-%d %H:%M:%S')
        seconds_parked = (datetime.now() - entry_time_dt).seconds
        blocks_of_10s = seconds_parked // 10
        base_fee, rate_per_10 = 0.50, 0.10
        total_due = base_fee + (blocks_of_10s * rate_per_10)
        
        st.write(f"⏱️ **Duration:** {seconds_parked} Seconds")
        st.write(f"💰 **Total Due:** RM {total_due:.2f}")
        
        if st.button("Confirm & Pay Now", type="primary", use_container_width=True):
            with st.spinner("Connecting to Gateway..."):
                time.sleep(1.5) # Realistic short delay
                supabase.table("slots").update({"status": "Vacant", "start_time": None}).eq("slot_id", entered_slot).execute()
                st.balloons()
                st.success("✅ Payment Successful! Gate will open shortly.")
                time.sleep(2) # Show message for 2 seconds
                st.session_state.show_payment = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. LAYOUT GRID ---
if not df_slots.empty:
    wings = sorted(df_slots['wing_id'].unique())
    selected_wing = st.radio("Select Level", wings, horizontal=True)
    
    wing_data = df_slots[df_slots['wing_id'] == selected_wing].sort_values(by='slot_id')
    html_grid = "<div class='parking-grid'>"
    for _, row in wing_data.iterrows():
        status = "occupied" if row['status'] == "Occupied" else "vacant"
        slot_num = row['slot_id'].split('-')[1]
        html_grid += f"<div class='slot {status}'>🚗<div class='slot-id'>{slot_num}</div></div>"
    html_grid += "</div>"
    st.markdown(html_grid, unsafe_allow_html=True)

time.sleep(3)
st.rerun()
