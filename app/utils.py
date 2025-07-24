import json


def load_tokens(server_name):
    try:
        if server_name == "IND":
            path = "tokens/ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "tokens/br.json"
        elif server_name == "PK":
            path = "tokens/pk.json"
        else:
            path = "tokens/bd.json"
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load tokens for {server_name}: {e}")
        return None

def get_server_url(server_name):
    """Get the appropriate server URL for the given server name"""
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com"
    elif server_name == "PK":
        return "https://clientbp.ggblueshark.com"
    else:
        return "https://clientbp.ggblueshark.com"
