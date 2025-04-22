import requests
import datetime
import concurrent.futures
from db_conn import connect_db

ROUTER_LIST_URL = "https://app.admiralplatform.com:YOUR_LIST_URL"
SPEED_TEST_URL = "https://app.admiralplatform.com:YOUR_SPEED_TEST_URL"

HEADERS = {
    "Authorization": "Bearer b286ace6e756a395893f54a84a8ef918",
    "x-api-key": "b286ace6e756a395893f54a84a8ef918",
    "API-Key": "b286ace6e756a395893f54a84a8ef918",
    "Content-Type": "application/json"
}

OFFSETS = [
    {"start": 0, "end": 39},
    {"start": 40, "end": 79}
]

session = requests.Session()
session.headers.update(HEADERS)

def format_date(date_str):
    """Convert API date format to MySQL DATETIME format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None

def sanitize_value(value, is_numeric=False):
    """Convert None to a default value."""
    if value is None:
        return 0 if is_numeric else None
    return value

def fetch_routers():
    """Fetch all routers with pagination using predefined offsets."""
    all_routers = []
    
    for range_set in OFFSETS:
        for offset in range(range_set["start"], range_set["end"] + 1, 100):
            url = f"{ROUTER_LIST_URL}?offset={offset}&limit=100"
            try:
                response = session.get(url)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and data:
                    all_routers.extend(data)
                
                print(f"✅ Fetched {len(data)} routers from offset {offset}")
            
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching routers at offset {offset}: {e}")
    
    return all_routers

def fetch_speed_tests(router):
    """Fetch speed test data using ether1mac."""
    ether1mac = router.get("ether1_mac")
    router_id = router.get("id")

    if not ether1mac:
        print(f"⚠️ Missing ether1mac for router: {router}")
        return []

    url = f"{SPEED_TEST_URL}?ether1mac={ether1mac}"
    
    try:
        response = session.get(url)
        response.raise_for_status()
        speed_test_data = response.json()

        if not speed_test_data:
            print(f"⚠️ No speed test data for router {ether1mac}")
            return []

        return [
            {
                "router_id": router_id,
                "date": format_date(entry.get("date")),
                "id": sanitize_value(entry.get("id"), is_numeric=True),  # Only using 'id'
                "download": sanitize_value(entry.get("download"), is_numeric=True),
                "upload": sanitize_value(entry.get("upload"), is_numeric=True),
                "latency1": sanitize_value(entry.get("latency1"), is_numeric=True),
                "latency2": sanitize_value(entry.get("latency2"), is_numeric=True),
                "latency3": sanitize_value(entry.get("latency3"), is_numeric=True),
                "protocol": sanitize_value(entry.get("protocol")),
                "company_id": sanitize_value(entry.get("company_id"), is_numeric=True),
                "management_name": sanitize_value(entry.get("management_name")),
            }
            for entry in speed_test_data
        ]
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ No data Available. {ether1mac}: {e}")
        return []

def get_existing_speed_test_ids():
    """Fetch existing speed test IDs from the database."""
    connection = connect_db()
    if not connection:
        print("❌ Failed to connect to the database.")
        return set()

    cursor = connection.cursor()
    existing_ids = set()

    try:
        cursor.execute("SELECT id FROM speed_test_tb")  # Fetch only 'id' column
        rows = cursor.fetchall()
        existing_ids = {row[0] for row in rows}
        print(f"📌 Found {len(existing_ids)} existing speed test IDs in DB.")

    except Exception as e:
        print(f"❌ Error fetching existing IDs: {e}")

    finally:
        cursor.close()
        connection.close()

    return existing_ids

def filter_new_data(data, existing_ids):
    """Filter only new speed test records that are not already in the database."""
    new_data = []
    for entry in data:
        if entry["id"] not in existing_ids:  # Compare API 'id' with existing DB 'id'
            new_data.append(entry)
        else:
            print(f"⚠️ Duplicate found (ID already exists): {entry['id']}")
    
    print(f"✅ Found {len(new_data)} new speed test records to insert.")
    return new_data

def remove_duplicates(data):
    """Remove duplicate 'id' entries before inserting into MySQL."""
    unique_data = {}
    duplicate_count = 0
    for entry in data:
        entry_id = entry["id"]
        if entry_id in unique_data:
            print(f"⚠️ Duplicate detected and skipped: {entry_id}")
            duplicate_count += 1
            continue
        unique_data[entry_id] = entry
    
    print(f"⚠️ {duplicate_count} duplicates removed.")
    return list(unique_data.values())


def insert_speed_test_data(data):
    """Insert speed test data into MySQL database using ON DUPLICATE KEY UPDATE."""
    if not data:
        print("⚠️ No speed test data to insert.")
        return

    connection = connect_db()
    if not connection:
        print("❌ Failed to connect to the database.")
        return

    cursor = connection.cursor()

    query = """
    INSERT INTO `speed_test_tb` 
    (`router_id`, `date`, `id`, `download_speed_mbps`, `upload_speed_mbps`, 
    `latency1_ms`, `latency2_ms`, `latency3_ms`, `protocol`, `company_id`, `management_name`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    `download_speed_mbps` = VALUES(`download_speed_mbps`),
    `upload_speed_mbps` = VALUES(`upload_speed_mbps`),
    `latency1_ms` = VALUES(`latency1_ms`),
    `latency2_ms` = VALUES(`latency2_ms`),
    `latency3_ms` = VALUES(`latency3_ms`),
    `protocol` = VALUES(`protocol`),
    `company_id` = VALUES(`company_id`),
    `management_name` = VALUES(`management_name`)
    """

    try:
        for entry in data:
            print(f"🔄 Inserting: {entry}")
            cursor.execute(query, (
                entry["router_id"], entry["date"], entry["id"], entry["download"],
                entry["upload"], entry["latency1"], entry["latency2"], entry["latency3"],
                entry["protocol"], entry["company_id"], entry["management_name"]
            ))

        connection.commit()
        print(f"✅ Inserted {len(data)} new speed test records into MySQL.")
    
    except Exception as e:
        print(f"❌ SQL Error: {e}")
    
    finally:
        cursor.close()
        connection.close()

def main():
    """Main function to fetch and store speed test data."""
    routers = fetch_routers()
    if not routers:
        print("⚠️ No routers found!")
        return

    # Fetch data concurrently
    speed_test_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        speed_results = executor.map(fetch_speed_tests, routers)

    # Flatten the results into a single list
    for result in speed_results:
        speed_test_data.extend(result)

    # ✅ Remove duplicates and filter only new data before inserting
    existing_ids = get_existing_speed_test_ids()  # Get the existing IDs from the database
    speed_test_data = filter_new_data(speed_test_data, existing_ids)
    speed_test_data = remove_duplicates(speed_test_data)  # Remove any internal duplicates

    # Insert data into database
    insert_speed_test_data(speed_test_data)

if __name__ == "__main__":
    main()
