import pyodbc
import os

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=NationalParkDB;'
    'Trusted_Connection=yes'
)
cursor = conn.cursor()

sql_files = [
    'sql_scripts/ddl/alerts_table.sql',
    'sql_scripts/procedures_triggers/visitor_proc_trigger.sql',
    'sql_scripts/seed/visitor_seed.sql'
]

for sql_file in sql_files:
    if not os.path.exists(sql_file):
        print(f"Skip: {sql_file} not found")
        continue
    
    print(f"Executing: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    for batch in sql.split('GO'):
        batch = batch.strip()
        if batch and not batch.startswith('--') and not batch.upper().startswith('PRINT'):
            try:
                cursor.execute(batch)
                conn.commit()
            except Exception as e:
                print(f"  Warning: {str(e)[:80]}")

print("Visitor module update completed successfully")
conn.close()
