import json


def load_tokens(server_name):
    try:
        if server_name == "IND":
            path = "tokens/ind.json"
        elif server_name == "PK":
            path = "tokens/pk.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "tokens/br.json"
        elif server_name == "BD":
            path = "tokens/bd.json"
        elif server_name == "SG":
            path = "tokens/sg.json"
        else:
            path = "tokens/bd.json"
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None
