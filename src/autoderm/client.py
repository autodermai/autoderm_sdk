import requests
from PIL import Image
import io

from api_call import parse_api_calls

class AutodermClient:
    def __init__(self, api_key, base_url='https://autoderm.ai'):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {api_key}'}

    def make_request(self, endpoint, method='GET', **kwargs):
        url = f'{self.base_url}/{endpoint}'
        response = requests.request(method, url, headers=self.headers, **kwargs)
        return response.json()
    

    # Endpoint
    # @ api_call_id: Single ID of ApiKeyUsage
    # @ api_call_ids: list[i32] of IDs of ApiKeyUsage
    # @ ad_uuid: UUID of a guest user
    # @ start_period TODO
    # @ end_period TODO
    def get_api_calls(self, api_call_id=None, api_call_ids=None, ad_uuid=None):

        # send the query
        params = {"language": "en"}
        if ad_uuid is not None:
            params["ad_uuid"] = ad_uuid
        if api_call_id is not None:
            params["api_call_id"] = api_call_id
        if api_call_ids is not None:
            params["api_call_ids"] = ','.join(map(str, api_call_ids))

        # Send the query
        response = requests.post(
            self.base_url + '/v1/get_api_calls/',
            headers={"Api-Key": self.api_key},
            params=params
        )
            
        print(response._content)
        if response.status_code != 200:
            print(f'status_error: {response.status_code}')
            return response.status_code
        else:
            
            api_calls, failed_ids = parse_api_calls(response.content.decode())

            print(f'Got {len(api_calls)} api_calls', end='')

            if failed_ids:
                print(f', and {len(failed_ids)} failed retrievals')
            else:
                print('')

            return api_calls, failed_ids
        

    def get_image(self, api_call_id):
        # send the query
        response = requests.get(
            self.base_url + '/v1/get_image',
            headers={"Api-Key": self.api_key},
            params={"language": "en", "api_call_id": api_call_id}
        )
            
        print(response._content)
        if response.status_code != 200:
            print(f'status_error: {response.status_code}')
            return response.status_code
        else:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image