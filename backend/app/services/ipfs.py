import ipfshttpclient
from typing import Dict, Any
import json
from app.core.config import settings

class IPFSService:
    def __init__(self):
        auth = f"{settings.IPFS_PROJECT_ID}:{settings.IPFS_PROJECT_SECRET}"
        self.client = ipfshttpclient.connect(
            settings.IPFS_API_URL,
            auth=auth
        )
    
    async def store_event_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Stores event metadata on IPFS and returns the hash
        """
        # Convert metadata to JSON string
        json_data = json.dumps(metadata)
        
        # Add to IPFS
        result = await self.client.add(json_data)
        return result['Hash']
    
    async def get_event_metadata(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieves event metadata from IPFS
        """
        # Get data from IPFS
        data = await self.client.cat(ipfs_hash)
        return json.loads(data)

ipfs_service = IPFSService()