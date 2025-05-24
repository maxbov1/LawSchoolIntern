import sys
import os

# Add parent /app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # now this will work

def test_routes():
    client = app.test_client()

    routes_to_test = [
        ('GET', '/'),
        ('GET', '/home'),
        ('GET', '/login'),
        ('GET', '/logout'),
        ('GET', '/upload'),
        ('GET', '/config'),
        ('GET', '/predictions'),
        ('GET', '/predict/test-model'),  # dummy test name
        ('GET', '/edit-permissions')
    ]

    print("\n🔍 Route Test Results:\n")
    for method, route in routes_to_test:
        try:
            response = client.open(route, method=method)
            code = response.status_code
            status = "✅ OK" if code in (200, 302) else "❌ ERROR"
            print(f"{method:4} {route:25} → {code} {status}")
            if route == '/config':
                print(f"config route: {response}")
        except Exception as e:
            print(f"{method:4} {route:25} → ❌ EXCEPTION: {str(e)}")

if __name__ == "__main__":
    test_routes()

