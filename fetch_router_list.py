import requests
import mysql.connector
import datetime

from db_conn import connect_db


API_URL = "https://app.admiralplatform.com:YOUR_LIST_URL"
HEADERS = {
    "Authorization": "YOUR_AUTH",
    "x-api-key": "YOUR_X-API-KEY",
    "API-Key": "YOUR_API-KEY",
    "Content-Type": "application/json"
}

# Define offset ranges
OFFSETS = [
    {"start": 0, "end": 39},
    {"start": 40, "end": 79}
]

def fetch_data_with_pagination():
    """Fetch all paginated data from API."""
    all_data = []
    
    for range_set in OFFSETS:
        for offset in range(range_set["start"], range_set["end"] + 1, 100):
            url = f"{API_URL}?offset={offset}&limit=100"
            try:
                response = requests.get(url, headers=HEADERS)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and data:
                    all_data.extend(data)  # Merge paginated results
                
                print(f"Fetched {len(data)} records from offset {offset}")

            except Exception as e:
                print(f"Error fetching offset {offset}: {e}")
             #   with open("cron_log.txt", "a") as log_file:
             #       log_file.write(f"{datetime.datetime.now()} - Error fetching offset {offset}: {e}\n")

    return all_data

def process_and_store_data(data):
    """Insert or update routers in MySQL."""
    if not data:
        print("No new data to process.")
        return
    
    try:
        # Connect to MySQL
        with mysql.connector.connect(**connect_db) as conn:
            with conn.cursor(dictionary=True) as cursor:
                for item in data:
                    router_id = item.get("id")
                    name = item.get("name")
                    user_group = item.get("user_group")
                    group_id = item.get("group_id")
                    latitude = item.get("lat")
                    longitude = item.get("long")

                    if not router_id:
                        print("Skipping entry: Missing router_id")
                        continue  

                    # Check if router_id exists
                    cursor.execute("SELECT * FROM router_list_tb WHERE router_id = %s", (router_id,))
                    existing_record = cursor.fetchone()

                    if existing_record:
                        # Update only if data changed
                        if (existing_record["name"] != name or
                            existing_record["user_group"] != user_group or
                            existing_record["group_id"] != group_id or
                            existing_record["latitude"] != latitude or
                            existing_record["longitude"] != longitude):

                            sql_update = """
                                UPDATE router_list_tb 
                                SET name = %s, user_group = %s, 
                                    group_id = %s, latitude = %s, longitude = %s
                                WHERE router_id = %s
                            """
                            values = (name, user_group, group_id, latitude, longitude, router_id)
                            cursor.execute(sql_update, values)
                            conn.commit()
                            print(f"Updated existing router: {router_id}")

                    else:
                        # Insert new router
                        sql_insert = """
                            INSERT INTO router_list_tb (router_id, name, user_group, group_id, latitude, longitude) 
                            VALUES ( %s, %s, %s, %s, %s, %s)
                        """
                        values = (router_id, name, user_group, group_id, latitude, longitude)
                        cursor.execute(sql_insert, values)
                        conn.commit()
                        print(f"Inserted new router: {router_id}")

                        # Log new router insert
                      #  with open("cron_log.txt", "a") as log_file:
                      #      log_file.write(f"{datetime.datetime.now()} - New router added: {router_id}, {school_name}\n")

        print("ADMIRAL Routers refreshed successfully!")

    except Exception as e:
        print("Database Error:", e)
      #  with open("cron_log.txt", "a") as log_file:
      #      log_file.write(f"{datetime.datetime.now()} - Database Error: {str(e)}\n")

if __name__ == "__main__":
    fetched_data = fetch_data_with_pagination()
    process_and_store_data(fetched_data)
