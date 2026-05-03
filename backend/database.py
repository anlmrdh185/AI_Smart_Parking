import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_slot_status(wing_id, slot_id, new_status):
    """
    Called by detector.py. 
    wing_id: identifies the stream (W1, W5, M10, etc.)
    slot_id: identifies the specific box (W1-01, etc.)
    new_status: 'Occupied' or 'Vacant'
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Determine table based on the first letter of wing_id
    if wing_id.startswith("W"):
        table_name = "Queensbay_Parking"
    elif wing_id.startswith("M"):
        table_name = "UsmMosque_Parking"
    else:
        print(f"❌ Error: Unknown wing prefix for {wing_id}")
        return

    try:
        if new_status == "Occupied":
            # Update the specific wing and slot in the parking table
            supabase.table(table_name).update({
                'status': 'Occupied', 
                'start_time': now
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
            print(f"☁️ Cloud Update: {wing_id} | {slot_id} is Occupied")
        
        elif new_status == "Vacant":
            # 1. Get the entry time first to create a transaction record
            response = supabase.table(table_name).select('start_time').eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
            
            if response.data and response.data[0].get('start_time'):
                entry_time = response.data[0]['start_time']
                
                # 2. Insert into transactions table with wing_id (W1, M10, etc.)
                supabase.table('transactions').insert({
                    'wing_id': wing_id,   # Records exactly which wing it came from
                    'slot_id': slot_id,
                    'entry_time': entry_time,
                    'exit_time': now,
                    'payment_status': 'Unpaid'
                }).execute()

            # 3. Reset the slot to Vacant
            supabase.table(table_name).update({
                'status': 'Vacant', 
                'start_time': None
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
            print(f"☁️ Cloud Update: {wing_id} | {slot_id} is Vacant")
            
    except Exception as e:
        print(f"❌ Supabase Error: {e}")
