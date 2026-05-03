import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Change function name to 'update_slot_status' so detector.py can find it
def update_slot_status(location_code, slot_id, new_status):
    """
    Function called by detector.py and detector_m.py to update the cloud database.
    location_code: 'W' for Queensbay, 'M' for USM
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Determine which table to use based on location_code
    if location_code.startswith("W"):
        table_name = "Queensbay_Parking"
    elif location_code.startswith("M"):
        table_name = "UsmMosque_Parking"
    else:
        print(f"❌ Error: Invalid location code '{location_code}'")
        return None

    try:
        if new_status == "Occupied":
            # 1. Update Cloud Status to Occupied and set the start_time
            response = supabase.table(table_name).update({
                'status': 'Occupied', 
                'start_time': now
            }).eq('slot_id', slot_id).execute()
            print(f"☁️ Cloud Update: {table_name} Slot {slot_id} is now Occupied at {now}")
        
        elif new_status == "Vacant":
            # 1. Get the start_time from the cloud before clearing it
            response = supabase.table(table_name).select('start_time').eq('slot_id', slot_id).execute()
            
            if response.data and response.data[0].get('start_time'):
                entry_time = response.data[0]['start_time']
                
                # 2. Log the completed session to a 'transactions' table
                try:
                    supabase.table('transactions').insert({
                        'location': table_name,
                        'slot_id': slot_id,
                        'entry_time': entry_time,
                        'exit_time': now
                    }).execute()
                except:
                    pass 

            # 3. Reset the slot to Vacant in the cloud
            supabase.table(table_name).update({
                'status': 'Vacant', 
                'start_time': None
            }).eq('slot_id', slot_id).execute()
            print(f"☁️ Cloud Update: {table_name} Slot {slot_id} is now Vacant")
            
    except Exception as e:
        print(f"❌ Error updating Supabase: {e}")
