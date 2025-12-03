import requests
import json

url = "https://wazgoplarevypdfbgeau.supabase.co/functions/v1/generate-game"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhemdvcGxhcmV2eXBkZmJnZWF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1ODU2MzAsImV4cCI6MjA4MDE2MTYzMH0.jxM3I8Tul-YszD6rd8asfpqHZCHo1bInScdK74d2s5I",
    "Content-Type": "application/json"
}
data = {"title": "Test Game"}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
