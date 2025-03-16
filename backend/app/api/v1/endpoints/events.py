from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.blockchain import blockchain_service
from app.services.ipfs import ipfs_service
from app.core.security import get_current_user
from app.schemas.event import EventCreate, EventResponse
from app.services.redis_cache import redis_cache

router = APIRouter()

@router.post("/events/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user = Depends(get_current_user)
):
    """
    Create a new ad event
    """
    try:
        # Store metadata in IPFS
        metadata = {
            "ip_address": event.ip_address,
            "device_info": event.device_info,
            "location": event.location,
            "timestamp": event.timestamp,
            "advertiser_id": current_user.id
        }
        ipfs_hash = await ipfs_service.store_event_metadata(metadata)
        
        # Log event to blockchain
        tx_hash = await blockchain_service.log_event(
            event.event_type,
            ipfs_hash
        )
        
        # Cache event data in Redis
        await redis_cache.set_event(tx_hash, {
            **metadata,
            "ipfs_hash": ipfs_hash,
            "transaction_hash": tx_hash
        })
        
        return {
            "transaction_hash": tx_hash,
            "ipfs_hash": ipfs_hash,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create event: {str(e)}"
        )

@router.get("/events/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str,
    current_user = Depends(get_current_user)
):
    """
    Retrieve an event by ID
    """
    try:
        # Check Redis cache first
        cached_event = await redis_cache.get_event(event_id)
        if cached_event:
            return cached_event
        
        # Get event from blockchain
        event = await blockchain_service.get_event(event_id)
        
        # Get metadata from IPFS
        metadata = await ipfs_service.get_event_metadata(event['ipfsHash'])
        
        # Combine blockchain and IPFS data
        full_event = {**event, **metadata}
        
        # Cache the result
        await redis_cache.set_event(event_id, full_event)
        
        return full_event
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve event: {str(e)}"
        )

@router.get("/events/", response_model=List[Dict[str, Any]])
async def list_events(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """
    List events with pagination
    """
    try:
        events = await redis_cache.get_recent_events(skip, limit)
        return events
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list events: {str(e)}"
        )