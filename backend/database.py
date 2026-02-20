import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
# Replace these with your actual Supabase URL and Anon Key
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_slot_status(wing_id, slot_id, new_status):
    """Function called by detector.py to update the cloud database"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        if new_status == "Occupied":
            # 1. Update Cloud Status to Occupied
            supabase.table('slots').update({
                'status': 'Occupied', 
                'start_time': now
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).eq('status', 'Vacant').execute()
            print(f"☁️ Cloud Update: {slot_id} is Occupied")
        
        elif new_status == "Vacant":
            # 1. Get the entry time from the cloud
            response = supabase.table('slots').select('start_time').eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
            
            if response.data and response.data[0].get('start_time'):
                entry_time = response.data[0]['start_time']
                
                # 2. Log 'Park and Run' Transaction to the cloud
                supabase.table('transactions').insert({
                    'wing_id': wing_id,
                    'slot_id': slot_id,
                    'entry_time': entry_time,
                    'exit_time': now,
                    'payment_status': 'Unpaid'
                }).execute()

            # 3. Reset the slot to Vacant in the cloud
            supabase.table('slots').update({
                'status': 'Vacant', 
                'start_time': None
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
            print(f"☁️ Cloud Update: {slot_id} is Vacant")
            
    except Exception as e:
        print(f"Error updating Supabase: {e}")