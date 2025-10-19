"""
Simple test script to query the RAG server and see if it works
"""
import requests
import json

# Test query
url = "http://localhost:9621/query"
data = {
    "query": "What are the evaluation factors?",
    "mode": "hybrid"
}

print("=" * 70)
print("Testing RAG Query")
print("=" * 70)
print(f"URL: {url}")
print(f"Query: {data['query']}")
print(f"Mode: {data['mode']}")
print("\nSending request...")
print("=" * 70)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS! Query worked!")
        print("\nResponse preview:")
        print("-" * 70)
        response_text = result.get('response', 'No response field')
        if len(response_text) > 500:
            print(response_text[:500] + "...")
        else:
            print(response_text)
        print("-" * 70)
    else:
        print(f"\n❌ ERROR: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to server")
    print("   Make sure the server is running on http://localhost:9621")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 70)
print("Check the SERVER TERMINAL for detailed error logs")
print("=" * 70)
