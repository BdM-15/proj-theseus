"""
Test script to upload Navy MBOS RFP to the RAG-Anything server
"""
import requests
import time
from pathlib import Path

# Configuration
SERVER_URL = "http://localhost:9621"
RFP_PATH = Path("inputs/__enqueued__/_N6945025R0003.pdf")

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{SERVER_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_stats():
    """Test the stats endpoint"""
    print("\n📊 Getting server statistics...")
    response = requests.get(f"{SERVER_URL}/stats")
    print(f"   Status: {response.status_code}")
    stats = response.json()
    print(f"   Working directory: {stats.get('working_dir')}")
    print(f"   Multimodal enabled: {stats.get('multimodal_enabled')}")
    return response.status_code == 200

def upload_rfp():
    """Upload the Navy MBOS RFP"""
    print("\n📤 Uploading Navy MBOS RFP...")
    print(f"   File: {RFP_PATH}")
    print(f"   Size: {RFP_PATH.stat().st_size / 1024:.1f} KB")
    
    if not RFP_PATH.exists():
        print(f"   ❌ File not found: {RFP_PATH}")
        return False
    
    # Upload the file
    with open(RFP_PATH, "rb") as f:
        files = {"file": (RFP_PATH.name, f, "application/pdf")}
        print(f"   ⏳ Processing... (this may take 10-15 minutes)")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{SERVER_URL}/upload",
                files=files,
                timeout=1800  # 30 minute timeout
            )
            elapsed = time.time() - start_time
            
            print(f"\n   ✅ Upload completed in {elapsed/60:.1f} minutes")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n   📋 Results:")
                print(f"      Filename: {result.get('filename')}")
                print(f"      Processing time: {result.get('processing_time_seconds', 0):.1f}s")
                print(f"      Entities extracted: {result.get('entities_extracted', 0)}")
                print(f"      Message: {result.get('message')}")
                return True
            else:
                print(f"   ❌ Upload failed: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Request timed out after 30 minutes")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

def test_query():
    """Test querying the uploaded RFP"""
    print("\n❓ Testing query endpoint...")
    
    queries = [
        "What are the key evaluation factors in Section M?",
        "What deliverables are required in Section F?",
        "What is the contract type and who is the contracting officer?"
    ]
    
    for i, query_text in enumerate(queries, 1):
        print(f"\n   Query {i}: {query_text}")
        
        try:
            response = requests.post(
                f"{SERVER_URL}/query",
                json={
                    "query": query_text,
                    "mode": "hybrid"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response received ({result.get('response_time_seconds', 0):.2f}s)")
                answer = result.get('answer', '')
                print(f"   📝 Answer: {answer[:200]}...")
            else:
                print(f"   ❌ Query failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 Testing GovCon Capture Vibe RAG-Anything Integration")
    print("=" * 70)
    
    # Test health
    if not test_health():
        print("\n❌ Server is not healthy. Please check if it's running.")
        return
    
    # Test stats
    test_stats()
    
    # Upload RFP
    if upload_rfp():
        # Test queries
        test_query()
    
    print("\n" + "=" * 70)
    print("✅ Testing complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
