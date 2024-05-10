from datetime import datetime
import json

# ApiCall Information without META information
class ApiCall:
    def __init__(self, id, user_id, timestamp, image_location, predictions, model):
        self.id = id
        self.user_id = user_id
        self.timestamp = timestamp
        self.image_location = image_location
        self.predictions = predictions
        self.model = model

    def __str__(self):
        return f"ApiCall(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp}, image_location={self.image_location}, predictions={self.predictions}, model={self.model})"

def parse_api_calls(json_data):
    api_calls = []
    results = json.loads(json_data)#["results"]

    for result in results['api_key_usages']:
        id = result['id']
        user_id = result["user_id"]
        timestamp = datetime.fromisoformat(result["timestamp"])
        image_location = result["image_location"]
        predictions = result["predictions"]
        model = result["model"]
        api_calls.append(ApiCall(id, user_id, timestamp, image_location, predictions, model))
        
    return api_calls, results['failed_ids']


