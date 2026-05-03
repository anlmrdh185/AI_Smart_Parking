import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def update_slot_status(wing_id, slot_id, new_status):
    """Function called by detector.py and detector_m.py to update the cloud database"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # ==========================================
        # DYNAMIC ROUTING BASED ON WING ID PREFIX
        # ==========================================
        
        # Check if the wing_id starts with 'M' (e.g., M10, M11, M12)
        if wing_id.startswith("M"):
            if new_status == "Occupied":
                supabase.table('UsmMosque_Parking').update({
                    'status': 'Occupied', 
                    'start_time': now
                }).eq('slot_id', slot_id).execute()
                print(f"☁️ Cloud Update (USM_MOSQUE): {slot_id} is Occupied")
            
            elif new_status == "Vacant":
                supabase.table('UsmMosque_Parking').update({
                    'status': 'Vacant', 
                    'start_time': None
                }).eq('slot_id', slot_id).execute()
                print(f"☁️ Cloud Update (USM_MOSQUE): {slot_id} is Vacant")

        # Check if the wing_id starts with 'W' (e.g., W1, W3A, W8)
        elif wing_id.startswith("W"):
            if new_status == "Occupied":
                supabase.table('Queensbay_Parking').update({
                    'status': 'Occupied', 
                    'start_time': now
                }).eq('wing_id', wing_id).eq('slot_id', slot_id).eq('status', 'Vacant').execute()
                print(f"☁️ Cloud Update (QUEENSBAY): {slot_id} is Occupied")
            
            elif new_status == "Vacant":
                # Get entry time for transaction log
                response = supabase.table('Queensbay_Parking').select('start_time').eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
                
                if response.data and response.data[0].get('start_time'):
                    entry_time = response.data[0]['start_time']
                    
                    # Log Transaction
                    supabase.table('transactions').insert({
                        'wing_id': wing_id,
                        'slot_id': slot_id,
                        'entry_time': entry_time,
                        'exit_time': now,
                        'payment_status': 'Unpaid'
                    }).execute()

                supabase.table('slots').update({
                    'status': 'Vacant', 
                    'start_time': None
                }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()
                print(f"☁️ Cloud Update (QUEENSBAY): {slot_id} is Vacant")
                
        else:
            print(f"⚠️ Warning: Unknown wing prefix for {wing_id}. Database not updated.")

    except Exception as e:
        print(f"❌ Error updating Supabase for {slot_id}: {e}")
