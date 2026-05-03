import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def update_slot_status(wing_id, slot_id, new_status):
    """
    Called by detector.py or detector_m.py
    wing_id: W1, W5, M10, etc.
    slot_id: W1-01, M10-01, etc.
    new_status: 'Occupied' or 'Vacant'
    """

    # ✅ Normalize input (VERY IMPORTANT)
    wing_id = wing_id.strip().upper()
    slot_id = slot_id.strip().upper()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ✅ Determine table
    if wing_id.startswith("W"):
        table_name = "Queensbay_Parking"
    elif wing_id.startswith("M"):
        table_name = "UsmMosque_Parking"
    else:
        print(f"❌ Error: Unknown wing prefix for '{wing_id}'")
        return

    # ✅ Debug logs
    print(f"DEBUG → wing_id: '{wing_id}', slot_id: '{slot_id}', status: '{new_status}'")
    print(f"DEBUG → Using table: {table_name}")

    try:
        # ==========================
        # 🚗 WHEN SLOT IS OCCUPIED
        # ==========================
        if new_status == "Occupied":

            supabase.table(table_name).upsert({
                'wing_id': wing_id,
                'slot_id': slot_id,
                'status': 'Occupied',
                'start_time': now
            }).execute()

            print(f"☁️ Cloud Update: {wing_id} | {slot_id} → Occupied")

        # ==========================
        # 🚗 WHEN SLOT IS VACANT
        # ==========================
        elif new_status == "Vacant":

            # 1️⃣ Get previous start_time
            response = supabase.table(table_name) \
                .select('start_time') \
                .eq('wing_id', wing_id) \
                .eq('slot_id', slot_id) \
                .execute()

            entry_time = None

            if response.data and len(response.data) > 0:
                entry_time = response.data[0].get('start_time')

            # 2️⃣ Insert into transactions (ONLY if entry_time exists)
            if entry_time:
                supabase.table('transactions').insert({
                    'wing_id': wing_id,
                    'slot_id': slot_id,
                    'entry_time': entry_time,
                    'exit_time': now,
                    'payment_status': 'Unpaid'
                }).execute()

                print(f"💰 Transaction recorded for {wing_id} | {slot_id}")

            else:
                print(f"⚠️ No entry_time found for {wing_id} | {slot_id}")

            # 3️⃣ Reset slot to Vacant (UPSERT again)
            supabase.table(table_name).upsert({
                'wing_id': wing_id,
                'slot_id': slot_id,
                'status': 'Vacant',
                'start_time': None
            }).execute()

            print(f"☁️ Cloud Update: {wing_id} | {slot_id} → Vacant")

        else:
            print(f"❌ Invalid status: {new_status}")

    except Exception as e:
        print(f"❌ Supabase Error: {e}")
