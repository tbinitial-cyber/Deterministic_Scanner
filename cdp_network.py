from models import NetworkRequest, NetworkResponse, NetworkLoadingFinished, NetworkLoadingFailed

class CDPCapture:
    def __init__(self):
        self.requests: list[NetworkRequest] = []
        self.responses: list[NetworkResponse] = []
        self.loading_finished: list[NetworkLoadingFinished] = []
        self.loading_failed: list[NetworkLoadingFailed] = []

    async def attach(self, page):
        """Attaches to the page and listens to raw CDP network events."""
        client = await page.context.new_cdp_session(page)
        await client.send('Network.enable')
        
        client.on('Network.requestWillBeSent', self._on_request)
        client.on('Network.responseReceived', self._on_response)
        client.on('Network.loadingFinished', self._on_loading_finished)
        client.on('Network.loadingFailed', self._on_loading_failed)
        return client

    def _on_request(self, event):
        req = event.get('request', {})
        self.requests.append(NetworkRequest(
            request_id=event.get('requestId', ''),
            url=req.get('url', ''),
            method=req.get('method', ''),
            resource_type=event.get('type', ''),
            timestamp=event.get('timestamp', 0.0),
            headers=req.get('headers', {}),
            initiator=event.get('initiator', {})
        ))

    def _on_response(self, event):
        resp = event.get('response', {})
        self.responses.append(NetworkResponse(
            request_id=event.get('requestId', ''),
            url=resp.get('url', ''),
            status=resp.get('status', 0),
            mime_type=resp.get('mimeType', ''),
            timestamp=event.get('timestamp', 0.0),
            headers=resp.get('headers', {})
        ))
        
    def _on_loading_finished(self, event):
        self.loading_finished.append(NetworkLoadingFinished(
            request_id=event.get('requestId', ''),
            timestamp=event.get('timestamp', 0.0),
            encoded_data_length=event.get('encodedDataLength', 0.0)
        ))
        
    def _on_loading_failed(self, event):
        self.loading_failed.append(NetworkLoadingFailed(
            request_id=event.get('requestId', ''),
            timestamp=event.get('timestamp', 0.0),
            error_text=event.get('errorText', ''),
            canceled=event.get('canceled', False)
        ))
