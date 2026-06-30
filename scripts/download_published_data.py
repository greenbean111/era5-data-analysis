import os
import requests
import time

def download_alma_data():
    base_url = "https://alma.sc.eso.org/data/meteo/wsb/"
    output_dir = r"data/raw/alma_published"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    years = ["01", "02"]
    months = [f"{m:02d}" for m in range(1, 13)]
    
    for year in years:
        for month in months:
            filename = f"wsb_{year}{month}.met"
            file_url = f"{base_url}{filename}"
            target_path = os.path.join(output_dir, filename)
            
            if os.path.exists(target_path):
                print(f"File {filename} already exists, skipping.")
                continue
                
            print(f"Downloading {filename} from {file_url}...")
            try:
                response = requests.get(file_url, timeout=30)
                if response.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(response.content)
                    print(f"Successfully downloaded {filename}")
                else:
                    print(f"Failed to download {filename}: Status {response.status_code}")
                # Be polite to the server
                time.sleep(0.5)
            except Exception as e:
                print(f"Error downloading {filename}: {e}")

if __name__ == "__main__":
    download_alma_data()
