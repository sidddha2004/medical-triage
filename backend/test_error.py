import urllib.request
import urllib.error
try:
    urllib.request.urlopen('http://127.0.0.1:8000/admin/')
    print("Success")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print("STATUS", e.code)
    print("BODY START:")
    print(body[:2000])
except Exception as e:
    print(e)
