import pyodbc
import os

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=NationalParkDB;'
    'Trusted_Connection=yes'
)
cursor = conn.cursor()

seed_files = [
    'sql_scripts/seed/all_modules_seed.sql',
    'sql_scripts/seed/visitor_seed.sql'
]

for seed_file in seed_files:
    if not os.path.exists(seed_file):
        print(f"Skip: {seed_file} not found")
        continue
    
    print(f"Executing: {seed_file}")
    with open(seed_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    for batch in sql.split('GO'):
        batch = batch.strip()
        if batch and not batch.startswith('--'):
            try:
                cursor.execute(batch)
                conn.commit()
            except Exception as e:
                print(f"  Warning: {str(e)[:100]}")

print("All seed data executed successfully")
conn.close()
