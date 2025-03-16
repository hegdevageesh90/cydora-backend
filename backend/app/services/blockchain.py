from web3 import Web3
from eth_account import Account
from eth_typing import Address
from typing import Optional, Dict, Any
import json
from pathlib import Path

from app.core.config import settings

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
        self.account = Account.from_key(settings.WALLET_PRIVATE_KEY)
        
        # Load contract ABI
        contract_path = Path(__file__).parent / "../contracts/AdEventLogger.json"
        with open(contract_path) as f:
            contract_json = json.load(f)
        
        self.contract = self.w3.eth.contract(
            address=settings.CONTRACT_ADDRESS,
            abi=contract_json["abi"]
        )
    
    async def log_event(self, event_type: int, ipfs_hash: str) -> str:
        """
        Logs an ad event to the blockchain
        Returns the transaction hash
        """
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        # Build transaction
        transaction = self.contract.functions.logEvent(
            event_type,
            ipfs_hash
        ).build_transaction({
            'chainId': 137,  # Polygon Mainnet
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, settings.WALLET_PRIVATE_KEY
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt['transactionHash'].hex()
    
    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """
        Retrieves an event from the blockchain by its ID
        """
        event = await self.contract.functions.getEvent(event_id).call()
        return {
            'advertiser': event[0],
            'eventType': event[1],
            'ipfsHash': event[2],
            'timestamp': event[3],
            'isValid': event[4]
        }

blockchain_service = BlockchainService()