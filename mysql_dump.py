import mysql.connector
import json
import os
import csv
from datetime import datetime

# Database credentials
USER = "root"
PASSWORD = "password"
DATABASE = "mythredz"
OUTPUT_DIR = "/Users/joereger/Dropbox (Personal)/JoeregerJournalDataTool/mysql_data_exported/mythredz"

try:
    # Connect to the database
    conn = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor(dictionary=True)

    # Get list of all non-system tables
    cursor.execute("SHOW TABLES")
    tables = [row[f'Tables_in_{DATABASE}'] for row in cursor.fetchall()]

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def escape_special_characters(row):
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = value.replace('\n', '\\n').replace('\r', '\\r').replace('"', '""')
        return row

    # Export each table to JSON and CSV
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        try:
            # Export to JSON
            json_output_file = os.path.join(OUTPUT_DIR, f"{table}.json")
            with open(json_output_file, 'w') as json_outfile:
                json.dump(rows, json_outfile, indent=4, default=convert_datetime)

            # Export to CSV
            csv_output_file = os.path.join(OUTPUT_DIR, f"{table}.csv")
            if rows:
                with open(csv_output_file, 'w', newline='', encoding='utf-8') as csv_outfile:
                    writer = csv.DictWriter(csv_outfile, fieldnames=rows[0].keys(), quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    for row in rows:
                        escaped_row = escape_special_characters(row)
                        writer.writerow(escaped_row)
        except IOError as e:
            print(f"Error writing file for table {table}: {e}")

except mysql.connector.Error as err:
    print(f"Database error: {err}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

print("Export completed.")