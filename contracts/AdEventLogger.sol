// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title AdEventLogger
 * @dev Contract for logging advertising events with fraud prevention mechanisms
 */
contract AdEventLogger is Ownable, Pausable, ReentrancyGuard {
    // Event types
    enum EventType { IMPRESSION, CLICK, CONVERSION }
    
    // Struct to store event details
    struct AdEvent {
        address advertiser;
        EventType eventType;
        string ipfsHash;
        uint256 timestamp;
        bool isValid;
    }
    
    // Mapping from event ID to AdEvent
    mapping(bytes32 => AdEvent) public events;
    
    // Event emitted when a new ad event is logged
    event AdEventLogged(
        bytes32 indexed eventId,
        address indexed advertiser,
        EventType eventType,
        string ipfsHash,
        uint256 timestamp
    );
    
    // Event emitted when an event is invalidated
    event EventInvalidated(bytes32 indexed eventId);
    
    // Rate limiting
    mapping(address => uint256) public lastEventTimestamp;
    uint256 public constant MIN_TIME_BETWEEN_EVENTS = 1 seconds;
    
    constructor() Ownable(msg.sender) {}
    
    /**
     * @dev Logs a new advertising event
     * @param eventType Type of the event (IMPRESSION, CLICK, CONVERSION)
     * @param ipfsHash IPFS hash containing additional event metadata
     * @return eventId Unique identifier for the logged event
     */
    function logEvent(
        EventType eventType,
        string calldata ipfsHash
    ) external nonReentrant whenNotPaused returns (bytes32) {
        require(
            block.timestamp - lastEventTimestamp[msg.sender] >= MIN_TIME_BETWEEN_EVENTS,
            "Rate limit exceeded"
        );
        
        bytes32 eventId = keccak256(
            abi.encodePacked(
                msg.sender,
                eventType,
                ipfsHash,
                block.timestamp
            )
        );
        
        require(events[eventId].timestamp == 0, "Event already exists");
        
        events[eventId] = AdEvent({
            advertiser: msg.sender,
            eventType: eventType,
            ipfsHash: ipfsHash,
            timestamp: block.timestamp,
            isValid: true
        });
        
        lastEventTimestamp[msg.sender] = block.timestamp;
        
        emit AdEventLogged(
            eventId,
            msg.sender,
            eventType,
            ipfsHash,
            block.timestamp
        );
        
        return eventId;
    }
    
    /**
     * @dev Invalidates a fraudulent event (only owner)
     * @param eventId ID of the event to invalidate
     */
    function invalidateEvent(bytes32 eventId) external onlyOwner {
        require(events[eventId].timestamp != 0, "Event does not exist");
        require(events[eventId].isValid, "Event already invalidated");
        
        events[eventId].isValid = false;
        emit EventInvalidated(eventId);
    }
    
    /**
     * @dev Pauses the contract
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpauses the contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Retrieves an event by ID
     * @param eventId ID of the event to retrieve
     * @return AdEvent struct containing event details
     */
    function getEvent(bytes32 eventId) external view returns (AdEvent memory) {
        require(events[eventId].timestamp != 0, "Event does not exist");
        return events[eventId];
    }
}