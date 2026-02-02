import requests; res = requests.post('http://127.0.0.1:8000/generate', json={'total_count': 5}); print(res.json())
