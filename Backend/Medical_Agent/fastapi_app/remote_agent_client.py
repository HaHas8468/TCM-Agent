import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

import httpx

load_dotenv()

logger = logging.getLogger(__name__)


class RemoteAgentClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url or os.getenv('AGENT_BASE_URL', '')
        self.api_key = api_key or os.getenv('AGENT_API_KEY', '')
        self.timeout = timeout
        self._client = None
        self._async_client = None

    def _get_client(self):
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self._client

    def _get_async_client(self):
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self._async_client

    def _get_headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def is_available(self) -> bool:
        if not self.base_url:
            return False
        try:
            response = self._get_client().get('/health')
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Remote agent health check failed: {str(e)}")
            return False

    def chat(self, session_id: str, patient_id: Optional[str], user_input: str, 
             mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = self._get_client().post('/agent/chat', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent chat error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent chat failed: {str(e)}")
            raise

    def classify(self, session_id: str, patient_id: Optional[str], user_input: str,
                 mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = self._get_client().post('/agent/classify', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent classify error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent classify failed: {str(e)}")
            raise

    def recommend(self, session_id: str, patient_id: Optional[str], user_input: str,
                 mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = self._get_client().post('/agent/recommend', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent recommend error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent recommend failed: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, Any]:
        payload = {"text": text}
        try:
            response = self._get_client().post('/diagnosis/extract-entities', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent extract_entities error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent extract_entities failed: {str(e)}")
            raise

    def classify_zheng(self, symptoms: List[str], tongue: Optional[List[str]] = None,
                       pulse: Optional[List[str]] = None, other_signs: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "symptoms": symptoms,
            "tongue": tongue or [],
            "pulse": pulse or [],
            "other_signs": other_signs or ""
        }
        try:
            response = self._get_client().post('/diagnosis/classify', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent classify_zheng error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent classify_zheng failed: {str(e)}")
            raise

    def knowledge_query(self, query_type: str, keyword: Optional[str] = "", 
                        params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "query_type": query_type,
            "keyword": keyword,
            "params": params or {}
        }
        try:
            response = self._get_client().post('/knowledge/query', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent knowledge_query error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent knowledge_query failed: {str(e)}")
            raise

    async def chat_async(self, session_id: str, patient_id: Optional[str], user_input: str,
                         mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = await self._get_async_client().post('/agent/chat', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent chat_async error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent chat_async failed: {str(e)}")
            raise

    async def classify_async(self, session_id: str, patient_id: Optional[str], user_input: str,
                           mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = await self._get_async_client().post('/agent/classify', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent classify_async error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent classify_async failed: {str(e)}")
            raise

    async def recommend_async(self, session_id: str, patient_id: Optional[str], user_input: str,
                           mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            response = await self._get_async_client().post('/agent/recommend', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent recommend_async error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent recommend_async failed: {str(e)}")
            raise

    async def extract_entities_async(self, text: str) -> Dict[str, Any]:
        payload = {"text": text}
        try:
            response = await self._get_async_client().post('/diagnosis/extract-entities', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent extract_entities_async error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent extract_entities_async failed: {str(e)}")
            raise

    async def classify_zheng_async(self, symptoms: List[str], tongue: Optional[List[str]] = None,
                                   pulse: Optional[List[str]] = None, other_signs: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "symptoms": symptoms,
            "tongue": tongue or [],
            "pulse": pulse or [],
            "other_signs": other_signs or ""
        }
        try:
            response = await self._get_async_client().post('/diagnosis/classify', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent classify_zheng_async error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent classify_zheng_async failed: {str(e)}")
            raise

    async def stream_chat(self, session_id: str, patient_id: Optional[str], user_input: str,
                          mode: str = "normal", scene: str = "guide", patient_profile: Optional[Dict[str, Any]] = None):
        payload = {
            "session_id": session_id,
            "patient_id": patient_id,
            "user_input": user_input,
            "mode": mode,
            "scene": scene
        }
        if patient_profile:
            payload["patient_profile"] = patient_profile
        try:
            async with self._get_async_client().stream('POST', '/agent/stream', json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote agent stream_chat error {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Remote agent stream_chat failed: {str(e)}")
            raise

    def close(self):
        if self._client:
            self._client.close()
        if self._async_client:
            asyncio.create_task(self._async_client.aclose())


remote_agent_client = RemoteAgentClient()
