import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CLOUD SETUP ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================
# 🚀 INITIALIZE ALL SLOTS (RUN ONCE START)
# =========================================
def initialize_slots(wing_id, total_slots):

    wing_id = wing_id.strip().upper()

    if wing_id.startswith("W"):
        table_name = "Queensbay_Parking"
    elif wing_id.startswith("M"):
        table_name = "UsmMosque_Parking"
    else:
        print(f"❌ Unknown wing: {wing_id}")
        return

    print(f"🚀 Initializing {wing_id} ({total_slots} slots) → {table_name}")

    for i in range(1, total_slots + 1):
        slot_id = f"{wing_id}-{str(i).zfill(2)}"

        try:
            supabase.table(table_name).upsert({
                'wing_id': wing_id,
                'slot_id': slot_id,
                'status': 'Vacant',
                'start_time': None
            }).execute()

            print(f"✅ {slot_id} ready")

        except Exception as e:
            print(f"❌ Error creating {slot_id}: {e}")


# =========================================
# 🔄 UPDATE SLOT STATUS (REAL-TIME)
# =========================================
def update_slot_status(wing_id, slot_id, new_status):

    wing_id = wing_id.strip().upper()
    slot_id = slot_id.strip().upper()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if wing_id.startswith("W"):
        table_name = "Queensbay_Parking"
    elif wing_id.startswith("M"):
        table_name = "UsmMosque_Parking"
    else:
        print(f"❌ Unknown wing: {wing_id}")
        return

    print(f"DEBUG → {wing_id} | {slot_id} → {new_status} ({table_name})")

    try:
        # ==========================
        # 🚗 OCCUPIED
        # ==========================
        if new_status == "Occupied":

            supabase.table(table_name).update({
                'status': 'Occupied',
                'start_time': now
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()

            print(f"☁️ {slot_id} → Occupied")

        # ==========================
        # 🚗 VACANT
        # ==========================
        elif new_status == "Vacant":

            # 1. Get entry time
            response = supabase.table(table_name) \
                .select('start_time') \
                .eq('wing_id', wing_id) \
                .eq('slot_id', slot_id) \
                .execute()

            entry_time = None

            if response.data:
                entry_time = response.data[0].get('start_time')

            # 2. Save transaction
            if entry_time:
                supabase.table('transactions').insert({
                    'wing_id': wing_id,
                    'slot_id': slot_id,
                    'entry_time': entry_time,
                    'exit_time': now,
                    'payment_status': 'Unpaid'
                }).execute()

                print(f"💰 Transaction saved: {slot_id}")

            # 3. Reset slot
            supabase.table(table_name).update({
                'status': 'Vacant',
                'start_time': None
            }).eq('wing_id', wing_id).eq('slot_id', slot_id).execute()

            print(f"☁️ {slot_id} → Vacant")

        else:
            print(f"❌ Invalid status: {new_status}")

    except Exception as e:
        print(f"❌ Supabase Error: {e}")
