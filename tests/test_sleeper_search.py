import requests
import json
import sys

def test_sleeper_search():
    # URL of your Flask backend
    base_url = "http://localhost:5000"
    
    # Use the provided session token
    session_token = "FrXaWummzehXgrL5FlCnmfZiOVTr0Nrfu1E_NxcvB7w"
    
    # Use a default username that we know exists
    username = input("Enter Sleeper username to search for (default: LordTokenizer): ") or "LordTokenizer"
    
    # Make the request
    try:
        response = requests.get(
            f"{base_url}/sleeper/search?username={username}",
            headers={"Authorization": session_token}
        )
        
        # Print response status and content
        print(f"Status Code: {response.status_code}")
        print("\nResponse Headers:")
        for header, value in response.headers.items():
            print(f"{header}: {value}")
        
        # Parse and pretty-print JSON response
        try:
            data = response.json()
            print("\nResponse Body:")
            print(json.dumps(data, indent=2))
            
            # Check if request was successful
            if data.get('success'):
                print("\n✅ Request successful!")
                user = data.get('user', {})
                leagues = data.get('leagues', [])
                
                print(f"\nFound user: {user.get('display_name')} (ID: {user.get('user_id')})")
                print(f"User has {len(leagues)} leagues:")
                
                for i, league in enumerate(leagues, 1):
                    print(f"  {i}. {league.get('name')} (ID: {league.get('league_id')})")
            else:
                print(f"\n❌ Request failed: {data.get('error')}")
                
        except json.JSONDecodeError:
            print("\nResponse is not valid JSON:")
            print(response.text)
    
    except requests.RequestException as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_sleeper_search() 