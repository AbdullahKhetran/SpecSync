"""
watsonx.py — IBM watsonx.ai LLM provider adapter.

Environment variables required (set in .env, never committed):
    WATSONX_API_KEY    — IBM Cloud API key
    WATSONX_PROJECT_ID — watsonx.ai project ID
    WATSONX_URL        — watsonx.ai endpoint URL
                         (default: https://us-south.ml.cloud.ibm.com)
    WATSONX_MODEL_ID   — model to use
                         (default: ibm/granite-3-3-8b-instruct)

Selected when LLM_PROVIDER=watsonx (the default).
"""

from __future__ import annotations

import json
import os

import httpx

# IAM token endpoint
_IAM_URL = "https://iam.cloud.ibm.com/identity/token"
_DEFAULT_URL = "https://us-south.ml.cloud.ibm.com"
_DEFAULT_MODEL = "ibm/granite-3-3-8b-instruct"


class WatsonxProvider:
    """IBM watsonx.ai provider — calls the text generation REST API."""

    def __init__(self) -> None:
        self._api_key = os.environ["WATSONX_API_KEY"]
        self._project_id = os.environ["WATSONX_PROJECT_ID"]
        self._base_url = os.environ.get("WATSONX_URL", _DEFAULT_URL).rstrip("/")
        self._model_id = os.environ.get("WATSONX_MODEL_ID", _DEFAULT_MODEL)
        self._iam_token: str | None = None

    # ------------------------------------------------------------------
    # IAM token (fetched lazily; re-used for the lifetime of one request)
    # ------------------------------------------------------------------

    async def _get_iam_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            _IAM_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self._api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    # ------------------------------------------------------------------
    # Core generate_json
    # ------------------------------------------------------------------

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:
        """Call watsonx.ai and return the raw JSON string."""
        async with httpx.AsyncClient() as client:
            token = await self._get_iam_token(client)

            # Build the full prompt following Granite instruct format
            prompt = (
                f"<|system|>\n{system_prompt}\n"
                f"<|user|>\n{user_prompt}\n"
                f"<|assistant|>\n"
            )

            payload = {
                "model_id": self._model_id,
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": 4096,
                    "temperature": 0.0,
                    "repetition_penalty": 1.05,
                },
                "project_id": self._project_id,
            }

            resp = await client.post(
                f"{self._base_url}/ml/v1/text/generation?version=2023-05-29",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
            resp.raise_for_status()

        data = resp.json()
        raw: str = data["results"][0]["generated_text"].strip()

        # Strip markdown code fences if the model wraps the JSON
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        return raw


# lazy import only needed for fence stripping
import re  # noqa: E402
