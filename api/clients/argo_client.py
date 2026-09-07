from typing import Any, Dict, Optional

import httpx

from config.settings import get_settings


class ArgoClientError(Exception):
    pass

class ArgoWorkflowClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"{self.settings.ARGO_SERVER}/api/v1/workflows/{self.settings.ARGO_NAMESPACE}"
        self.headers = {"Content-Type": "application/json"}
        if self.settings.ARGO_TOKEN:
            self.headers["Authorization"] = f"Bearer {self.settings.ARGO_TOKEN.get_secret_value()}"
            
    async def submit_workflow(self, parameters: Dict[str, Any]) -> str:
        """Submits a new workflow and returns workflow ID"""
        payload = {
            "namespace": self.settings.ARGO_NAMESPACE,
            "serverDryRun": False,
            "resourceKind": "WorkflowTemplate",
            "resourceName": self.settings.ARGO_WORKFLOW_TEMPLATE,
            "submitOptions": {
                "parameters": [f"{k}={v}" for k, v in parameters.items()]
            }
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/submit",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return data.get("metadata", {}).get("name")
            except httpx.HTTPStatusError as e:
                raise ArgoClientError(f"HTTP error {e.response.status_code}") from e
            except httpx.RequestError as e:
                raise ArgoClientError(f"Connection error: {e}") from e
                
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{workflow_id}",
                    headers=self.headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise ArgoClientError(f"Failed to get status: {e}") from e
