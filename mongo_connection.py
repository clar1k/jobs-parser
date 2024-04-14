from pymongo import MongoClient

def get_mongo_client():
    uri = ""
    client = MongoClient(uri)
    try:
        client.admin.command("ping")
        print("Succes with connection")
    except Exception:
        return None
    return client

if __name__ == '__main__':
  pass