import requests
import os
import posixpath
import time
from json import JSONDecodeError
from typing import Any, Dict, Iterator
from PIL import Image
import io

from httpx import Client, ConnectError, HTTPTransport, RequestError, Response

from autoderm.client_base import ClientBase
from autoderm.constants import ENDPOINT, RETRY_STATUS_CODES
from autoderm.exceptions import (
    AutodermAPIException,
    AutodermAPIStatusException,
    AutodermConnectionException,
    AutodermException,
)

from autoderm.api_call import parse_api_calls


class AutodermClient(ClientBase):
    """
    Synchronous wrapper around the async client
    """

    def __init__(
        self,
        api_key=os.environ.get("AUTODERM_API_KEY", None),
        endpoint: str = ENDPOINT,
        max_retries: int = 5,
        timeout: int = 120,
    ):
        super().__init__(endpoint, api_key, max_retries, timeout)

        self._client = Client(
            follow_redirects=True, timeout=self._timeout, transport=HTTPTransport(retries=self._max_retries)
        )

    def __del__(self) -> None:
        self._client.close()

    def _check_response_status_codes(self, response: Response) -> None:
        if response.status_code in RETRY_STATUS_CODES:
            raise AutodermAPIStatusException.from_response(
                response,
                message=f"Status: {response.status_code}. Message: {response.text}",
            )
        elif 400 <= response.status_code < 500:
            if response.stream:
                response.read()
            raise AutodermAPIException.from_response(
                response,
                message=f"Status: {response.status_code}. Message: {response.text}",
            )
        elif response.status_code >= 500:
            if response.stream:
                response.read()
            raise AutodermException(
                message=f"Status: {response.status_code}. Message: {response.text}",
            )

    def _check_streaming_response(self, response: Response) -> None:
        self._check_response_status_codes(response)

    def _check_response(self, response: Response) -> Dict[str, Any]:
        self._check_response_status_codes(response)

        json_response: Dict[str, Any] = response.json()

        if "object" not in json_response:
            raise AutodermException(message=f"Unexpected response: {json_response}")
        if "error" == json_response["object"]:  # has errors
            raise AutodermAPIException.from_response(
                response,
                message=json_response["message"],
            )

        return json_response

    def _request(
        self,
        method: str,
        json: Dict[str, Any],
        path: str,
        stream: bool = False,
        attempt: int = 1,
    ) -> Iterator[Dict[str, Any]]:
        accept_header = "text/event-stream" if stream else "application/json"
        headers = {
            "Accept": accept_header,
            "User-Agent": f"mistral-client-python/{self._version}",
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        url = posixpath.join(self._endpoint, path)

        self._logger.debug(f"Sending request: {method} {url} {json}")

        response: Response

        try:
            if stream:
                with self._client.stream(
                    method,
                    url,
                    headers=headers,
                    json=json,
                ) as response:
                    self._check_streaming_response(response)

                    for line in response.iter_lines():
                        json_streamed_response = self._process_line(line)
                        if json_streamed_response:
                            yield json_streamed_response

            else:
                response = self._client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                )

                yield self._check_response(response)

        except ConnectError as e:
            raise AutodermConnectionException(str(e)) from e
        except RequestError as e:
            raise AutodermException(f"Unexpected exception ({e.__class__.__name__}): {e}") from e
        except JSONDecodeError as e:
            raise AutodermAPIException.from_response(
                response,
                message=f"Failed to decode json body: {response.text}",
            ) from e
        except AutodermAPIStatusException as e:
            attempt += 1
            if attempt > self._max_retries:
                raise AutodermAPIStatusException.from_response(response, message=str(e)) from e
            backoff = 2.0**attempt  # exponential backoff
            time.sleep(backoff)

            # Retry as a generator
            for r in self._request(method, json, path, stream=stream, attempt=attempt):
                yield r
    
    # Make image prediction
    # todo: change image content to more pytonic object
    # now only English language
    def query(self, image_contents, model=None, save_image=True):

        # send the query
        response = requests.post(
            self._endpoint + "/v1/query",
            headers={"Api-Key": self._api_key},
            files={"file": image_contents},
            params={"language": "en", "simple_names": "True", "save_image": save_image, "model": model}
        )

        print(response._content)
        if response.status_code != 200:
            print(f'status_error: {response.status_code}')
            error_message = f'Status Error: {response.status_changed}'
            print(error_message)
            raise ValueError(error_message)
        else:
            # get the JSON data returned
            data = response.json()

            # get only the predictions
            predictions = data["predictions"]

            return predictions

    # Endpoint
    # @ api_call_id: Single ID of ApiKeyUsage
    # @ api_call_ids: list[i32] of IDs of ApiKeyUsage
    # @ ad_uuid: UUID of a guest user
    def get_api_calls(self, api_call_id=None, api_call_ids=None, ad_uuid=None, start_period=None, end_period=None, model=None, limit=None):

        # send the query
        params = {"language": "en"}
        if ad_uuid is not None:
            params["ad_uuid"] = ad_uuid
        if api_call_id is not None:
            params["api_call_id"] = api_call_id
        if api_call_ids is not None:
            params["api_call_ids"] = ','.join(map(str, api_call_ids))
        if start_period is not None:
            params["start_period"] = start_period
        if end_period is not None:
            params["end_period"] = end_period
        if model is not None:
            params["model"] = model
        if limit is not None:
            params["limit"] = limit

        # Send the query
        response = requests.post(
            self._endpoint + '/v1/get_api_calls/',
            headers={"Api-Key": self._api_key},
            params=params
        )
            
        if response.status_code != 200:
            print(f'status_error: {response.status_code}')
            raise AutodermAPIStatusException.from_response(response, message=f'Failed to perform API call: {response.content}')
        else:
            
            api_calls, failed_ids = parse_api_calls(response.content.decode())

            print(f'Got {len(api_calls)} api_calls', end='')

            if failed_ids:
                print(f', and {len(failed_ids)} failed retrievals')
            else:
                print('')

            return api_calls#, failed_ids
        

    def get_image(self, api_call_id):
        # send the query
        response = requests.get(
            self._endpoint + '/v1/get_image',
            headers={"Api-Key": self._api_key},
            params={"language": "en", "api_call_id": api_call_id}
        )
            
        if response.status_code != 200:
            print(f'status_error: {response.status_code}')
            return {response.status_code, response.content}
        else:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image