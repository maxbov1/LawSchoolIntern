import sys
import os

# Add parent /app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # now this will work

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['project_id'] = 'c012ebd1'
    response = client.get('/config')
    print(response.data.decode())
