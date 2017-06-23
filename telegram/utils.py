

def validate_fields(data, required_fields):
    for field in required_fields:
        if field not in data:
            return False
    return True