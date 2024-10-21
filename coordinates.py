import pandas as pd
import googlemaps
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Initialize the Google Maps API client with your API key
gmaps = googlemaps.Client(key='AIzaSyDAmk-iSIiU0QgSy_5ZeC3sfOX43FgOKng')

# Load the spreadsheet
file_path = 'coordinates_test.xlsx'
xls = pd.ExcelFile(file_path)
doctor_matching_df = pd.read_excel(xls, sheet_name='Doctor_Matching')

# Function to get latitude and longitude from an address with error handling
def get_lat_lon(address):
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lon = geocode_result[0]['geometry']['location']['lng']
            print(f"Successfully fetched lat/lon for {address}: ({lat}, {lon})")
            return lat, lon
        else:
            print(f"No results for {address}")
            return None, None
    except Exception as e:
        print(f"Error fetching data for address {address}: {e}")
        return None, None

# Function to handle requests in parallel
def geocode_addresses(addresses, max_workers=5):
    latitudes = []
    longitudes = []
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_lat_lon, address): address for address in addresses}
        for future in as_completed(futures):
            address = futures[future]
            try:
                lat, lon = future.result()
                latitudes.append(lat)
                longitudes.append(lon)
            except Exception as e:
                print(f"Error processing address {address}: {e}")
                latitudes.append(None)
                longitudes.append(None)
    
    return latitudes, longitudes

print("Starting geocoding process...")

# Split addresses into manageable chunks (Google Maps API has limits)
chunk_size = 10  # Adjust chunk size down to reduce pressure on the API
num_chunks = len(doctor_matching_df) // chunk_size + 1

all_latitudes = []
all_longitudes = []

for i in range(num_chunks):
    chunk = doctor_matching_df['Address'][i*chunk_size:(i+1)*chunk_size]
    print(f"Processing chunk {i+1} of {num_chunks}...")
    
    # Add extra logging to see the chunk of addresses being processed
    print(f"Addresses in this chunk: {list(chunk)}")

    latitudes, longitudes = geocode_addresses(chunk, max_workers=3)  # Lowered max_workers to 3
    all_latitudes.extend(latitudes)
    all_longitudes.extend(longitudes)
    
    # Optional delay to avoid rate limits
    print("Waiting 1 second before processing the next chunk...")
    time.sleep(1)

# Add the new columns for Latitude and Longitude to the dataframe
doctor_matching_df['Latitude'] = all_latitudes
doctor_matching_df['Longitude'] = all_longitudes

# Save the updated dataframe back to the Excel file
output_file_path = 'Doctor_Matching_With_Lat_Lon.xlsx'
doctor_matching_df.to_excel(output_file_path, index=False)

print(f"Process completed! Latitude and Longitude columns added successfully. The file has been saved as: {output_file_path}")
