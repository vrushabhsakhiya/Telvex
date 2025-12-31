import requests
import sys

def check_url(url):
    print(f"Checking {url}...")
    try:
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        
        # Look for traceback in text
        text = resp.text
        if "Traceback" in text:
            idx = text.find("Traceback")
            print("--- TRACEBACK FOUND ---")
            print(text[idx:idx+2000]) # Print 2000 chars of traceback
        else:
            print(f"Content Start: {text[:500]}")
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_url("http://127.0.0.1:5000/login")
