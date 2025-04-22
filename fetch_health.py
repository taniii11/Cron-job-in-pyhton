import requests
import datetime
import concurrent.futures
from db_conn import connect_db

ROUTER_LIST_URL = "https://app.admiralplatform.com:YOUR_LIST_URL"
ROUTER_HEALTH_URL = "https://app.admiralplatform.com:YOUR_ROUTER_HEALTH_URL"

HEADERS = {
    "Authorization": "YOUR_AUTH",
    "x-api-key": "YOUR_X-API-KEY",
    "API-Key": "YOUR_API-KEY",
    "Content-Type": "application/json"
}

OFFSETS = [
    {"start": 0, "end": 39},
    {"start": 40, "end": 79}
]

session = requests.Session()
session.headers.update(HEADERS)

def format_date(date_str):
    """Convert ISO 8601 date (YYYY-MM-DDTHH:MM) to MySQL DATETIME (YYYY-MM-DD HH:MM:SS)"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def fetch_routers():
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

            except Exception as e:
                print(f"❌ Error fetching routers at offset {offset}: {e}")
    
    return all_routers

def fetch_router_health(router):
    router_id = router.get("id")
    url = f"{ROUTER_HEALTH_URL}?router_id={router_id}"
    try:
        response = session.get(url)
        response.raise_for_status()
        health_data = response.json()

        if health_data and "month" in health_data and "ether1" in health_data["month"]:
            ether1_data = health_data["month"]["ether1"].get("data", [])

            return [
                {
                    "router_id": router_id,
                    "interface": "ether1",
                    "date": format_date(entry.get("date", "unknown")),
                    "download": entry.get("download", "unknown"),
                    "upload": entry.get("upload", "unknown"),
                    "cpu_usage": entry.get("cpu", "unknown"),
                    "ram_usage": entry.get("ram", "unknown"),
                    "disk_usage": entry.get("disk", "unknown"),
                }
                for entry in ether1_data
            ]
        
        return [{
            "router_id": router_id,
            "interface": "ether1",
            "date": None,
            "download": "No Data",
            "upload": "No Data",
            "cpu_usage": "No Data",
            "ram_usage": "No Data",
            "disk_usage": "No Data",
        }]

    except Exception as e:
        print(f"⚠️ NO DATA AVAILABLE. {router_id}: {e}")
        return [{
            "router_id": router_id,
            "interface": "ether1",
            "date": None,
            "download": "Error",
            "upload": "Error",
            "cpu_usage": "Error",
            "ram_usage": "Error",
            "disk_usage": "Error",
        }]

def insert_into_db(data):
    connection = connect_db()
    if not connection:
        print("❌ Failed to connect to the database.")
        return
    
    cursor = connection.cursor()

    query = """
    INSERT INTO `router_health_tb` (`router_id`, `interface`, `date`, `download`, `upload`, `cpu_usage`, `ram_usage`, `disk_usage`) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    for entry in data:
        cursor.execute(query, (
            entry["router_id"], 
            entry["interface"], 
            entry["date"], 
            entry["download"], 
            entry["upload"], 
            entry["cpu_usage"], 
            entry["ram_usage"], 
            entry["disk_usage"]
        ))

    connection.commit()
    cursor.close()
    connection.close()
    print("✅ Data successfully inserted into MySQL database.")

def main():
    routers = fetch_routers()
    if not routers:
        print("⚠️ No routers found!")
        return

    data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_router_health, routers))

    for result in results:
        data.extend(result)

    insert_into_db(data)

if __name__ == "__main__":
    main()
