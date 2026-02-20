import random
from datetime import datetime, timedelta
from supabase import create_client

# --- 1. SUPABASE CONNECTION ---
SUPABASE_URL = "https://edmusfoswgnjarzewzbi.supabase.co"
SUPABASE_KEY = "sb_publishable_P-od1ESelOgV9dXUKooIlQ_x3FrRWHE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Injecting 30 days of synthetic parking data into Supabase...")

wings = ['W1', 'W3A', 'W5', 'W7', 'W8']
now = datetime.now()

# Traffic weights (Hour of day: Weight). Higher weight = more cars park at this time.
hourly_weights = {
    6: 1, 7: 2, 8: 5, 9: 6, 10: 7, 11: 8, 
    12: 10, 13: 10, 14: 8, 15: 6, 16: 5, 17: 7, 
    18: 9, 19: 8, 20: 5, 21: 3, 22: 2, 23: 1
}

transactions = []
for _ in range(500): # Generate 500 past parking sessions
    # Pick a random day in the last 30 days
    days_ago = random.randint(1, 30)
    
    # Pick an hour based on our realistic weights
    hour = random.choices(list(hourly_weights.keys()), weights=list(hourly_weights.values()))[0]
    minute = random.randint(0, 59)
    
    # Create the entry and exit times
    entry_time = now - timedelta(days=days_ago)
    entry_time = entry_time.replace(hour=hour, minute=minute, second=0)
    
    # Cars stay between 30 mins and 4 hours
    stay_duration = timedelta(minutes=random.randint(30, 240))
    exit_time = entry_time + stay_duration
    
    transactions.append({
        'wing_id': random.choice(wings),
        'slot_id': f"{random.choice(wings)}-{random.randint(1, 10):02d}",
        'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
        'exit_time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
        'amount': round(random.uniform(2.0, 10.0), 2),
        'payment_status': 'Paid'
    })

# Send to Supabase in batches
for i in range(0, len(transactions), 100):
    supabase.table('transactions').insert(transactions[i:i+100]).execute()

print("✅ Successfully added 500 realistic records to your cloud database!")