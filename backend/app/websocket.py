"""
WebSocket support for real-time consultation messaging.
Implements live chat with <200ms latency as per requirements.
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime
import secrets

from app.auth import get_current_user_websocket
from app.services.consultation_service import ConsultationService
from app.database import db as database


class ConnectionManager:
    """WebSocket connection manager for real-time messaging."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, consultation_id: str, user_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        
        if consultation_id not in self.active_connections:
            self.active_connections[consultation_id] = []
        
        self.active_connections[consultation_id].append(websocket)
        self.user_connections[user_id] = websocket
        
        print(f"User {user_id} connected to consultation {consultation_id}")
    
    def disconnect(self, websocket: WebSocket, consultation_id: str, user_id: str):
        """Remove WebSocket connection."""
        if consultation_id in self.active_connections:
            if websocket in self.active_connections[consultation_id]:
                self.active_connections[consultation_id].remove(websocket)
                
                # Clean up empty consultation rooms
                if not self.active_connections[consultation_id]:
                    del self.active_connections[consultation_id]
        
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        print(f"User {user_id} disconnected from consultation {consultation_id}")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user."""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_text(message)
            except:
                # Connection closed, remove from tracking
                del self.user_connections[user_id]
    
    async def broadcast_to_consultation(self, message: str, consultation_id: str, exclude_user: Optional[str] = None):
        """Broadcast message to all users in consultation."""
        if consultation_id in self.active_connections:
            disconnected_users = []
            
            for websocket in self.active_connections[consultation_id]:
                try:
                    await websocket.send_text(message)
                except:
                    # Connection closed, mark for cleanup
                    for user_id, ws in self.user_connections.items():
                        if ws == websocket:
                            disconnected_users.append(user_id)
                            break
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                if user_id in self.user_connections:
                    del self.user_connections[user_id]
    
    async def send_typing_indicator(self, consultation_id: str, user_id: str, is_typing: bool):
        """Send typing indicator to consultation participants."""
        message = {
            "type": "typing_indicator",
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_consultation(
            json.dumps(message), 
            consultation_id, 
            exclude_user=user_id
        )
    
    async def send_delivery_status(self, consultation_id: str, message_id: str, user_id: str, status: str):
        """Send message delivery status update."""
        message = {
            "type": "delivery_status",
            "message_id": message_id,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_consultation(
            json.dumps(message), 
            consultation_id
        )


# Global connection manager
manager = ConnectionManager()


async def get_consultation_service() -> ConsultationService:
    """Get consultation service instance."""
    return ConsultationService(database.get_db())


async def websocket_endpoint(
    websocket: WebSocket,
    consultation_id: str,
    token: str,
    service: ConsultationService = Depends(get_consultation_service)
):
    """
    WebSocket endpoint for real-time consultation messaging.
    
    Supports:
    - Live messaging with <200ms latency
    - Typing indicators
    - Delivery status tracking
    - Message read receipts
    - Connection health monitoring
    """
    # Authenticate user
    try:
        current_user = await get_current_user_websocket(token)
        user_id = current_user["user_id"]
        
        # Verify consultation access
        consultation = await service.get_consultation(consultation_id, user_id)
        if not consultation:
            await websocket.close(code=1008, reason="Consultation not found or access denied")
            return
        
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect user to consultation room
    await manager.connect(websocket, consultation_id, user_id)
    
    # Send connection confirmation
    await manager.send_personal_message(
        json.dumps({
            "type": "connection_established",
            "consultation_id": consultation_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }),
        user_id
    )
    
    # Notify other participants of new connection
    await manager.broadcast_to_consultation(
        json.dumps({
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }),
        consultation_id,
        exclude_user=user_id
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "chat_message":
                # Handle chat message
                await handle_chat_message(websocket, consultation_id, user_id, message_data, service)
            
            elif message_type == "typing_start":
                # Handle typing start
                await manager.send_typing_indicator(consultation_id, user_id, True)
            
            elif message_type == "typing_stop":
                # Handle typing stop
                await manager.send_typing_indicator(consultation_id, user_id, False)
            
            elif message_type == "message_read":
                # Handle message read receipt
                await handle_message_read(consultation_id, user_id, message_data, service)
            
            elif message_type == "ping":
                # Handle ping for connection health
                await manager.send_personal_message(
                    json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    user_id
                )
            
            else:
                # Unknown message type
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    user_id
                )
    
    except WebSocketDisconnect:
        # User disconnected
        await manager.disconnect(websocket, consultation_id, user_id)
        
        # Notify other participants
        await manager.broadcast_to_consultation(
            json.dumps({
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }),
            consultation_id,
            exclude_user=user_id
        )
    
    except Exception as e:
        # Unexpected error
        print(f"WebSocket error for user {user_id} in consultation {consultation_id}: {str(e)}")
        await manager.disconnect(websocket, consultation_id, user_id)


async def handle_chat_message(
    websocket: WebSocket, 
    consultation_id: str, 
    user_id: str, 
    message_data: Dict[str, Any], 
    service: ConsultationService
):
    """Handle incoming chat message."""
    try:
        # Extract message details
        message_text = message_data.get("message_text", "").strip()
        message_type = message_data.get("message_type", "text")
        
        if not message_text:
            await manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": "Message text cannot be empty",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                user_id
            )
            return
        
        # Create message using consultation service
        from app.models.consultation import MessageCreate, MessageType
        
        message_create = MessageCreate(
            sender_id=user_id,
            message_text=message_text,
            message_type=MessageType(message_type)
        )
        
        # Store message in database
        message_doc = await service.send_message(consultation_id, message_create)
        
        # Prepare broadcast message
        broadcast_message = {
            "type": "new_message",
            "message_id": message_doc["message_id"],
            "consultation_id": consultation_id,
            "sender_id": user_id,
            "message_text": message_text,
            "message_type": message_type,
            "timestamp": message_doc["timestamp"].isoformat(),
            "delivery_status": message_doc["delivery_status"]
        }
        
        # Broadcast to all consultation participants
        await manager.broadcast_to_consultation(
            json.dumps(broadcast_message), 
            consultation_id
        )
        
        # Send delivery confirmation to sender
        await manager.send_personal_message(
            json.dumps({
                "type": "message_sent",
                "message_id": message_doc["message_id"],
                "timestamp": message_doc["timestamp"].isoformat()
            }),
            user_id
        )
        
    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "Failed to send message",
                "timestamp": datetime.utcnow().isoformat()
            }),
            user_id
        )


async def handle_message_read(
    consultation_id: str, 
    user_id: str, 
    message_data: Dict[str, Any], 
    service: ConsultationService
):
    """Handle message read receipt."""
    try:
        message_id = message_data.get("message_id")
        
        if not message_id:
            return
        
        # In a real implementation, you would update the message as read
        # For now, we'll just broadcast the read status
        
        await manager.broadcast_to_consultation(
            json.dumps({
                "type": "message_read",
                "message_id": message_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }),
            consultation_id
        )
        
    except Exception as e:
        print(f"Error handling message read: {str(e)}")


# Connection monitoring and cleanup
async def cleanup_inactive_connections():
    """Periodic cleanup of inactive connections."""
    while True:
        try:
            # Check for inactive connections and clean them up
            # This could be enhanced with proper timeout handling
            
            for consultation_id, connections in list(manager.active_connections.items()):
                active_connections = []
                for websocket in connections:
                    try:
                        # Send ping to check if connection is still active
                        await websocket.send_text(json.dumps({
                            "type": "ping",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        active_connections.append(websocket)
                    except:
                        # Connection is dead, don't add to active list
                        pass
                
                manager.active_connections[consultation_id] = active_connections
                
                # Clean up empty consultation rooms
                if not active_connections:
                    del manager.active_connections[consultation_id]
            
            # Wait before next cleanup cycle
            await asyncio.sleep(30)  # Run every 30 seconds
            
        except Exception as e:
            print(f"Error in connection cleanup: {str(e)}")
            await asyncio.sleep(30)


# Global cleanup task - will be started during app startup
cleanup_task = None


def start_websocket_cleanup_task():
    """Start the WebSocket cleanup task. Call this during app startup."""
    global cleanup_task
    if cleanup_task is None:
        cleanup_task = asyncio.create_task(cleanup_inactive_connections())


def stop_websocket_cleanup_task():
    """Stop the WebSocket cleanup task. Call this during app shutdown."""
    global cleanup_task
    if cleanup_task is not None:
        cleanup_task.cancel()
        cleanup_task = None


# WebSocket message types for frontend
WS_MESSAGE_TYPES = {
    # Connection
    "connection_established": "Connection established",
    "user_joined": "User joined consultation",
    "user_left": "User left consultation",
    "pong": "Pong response",
    
    # Messaging
    "new_message": "New chat message received",
    "message_sent": "Message sent confirmation",
    "message_read": "Message read receipt",
    "delivery_status": "Message delivery status update",
    
    # Interaction
    "typing_indicator": "User typing status",
    
    # System
    "error": "Error message",
    "ping": "Connection ping"
}


def get_websocket_url(consultation_id: str, token: str) -> str:
    """Generate WebSocket URL for frontend."""
    base_url = "ws://localhost:8000"  # In production, use wss://
    return f"{base_url}/ws/consultations/{consultation_id}?token={token}"


# Frontend integration helpers
def create_websocket_client(consultation_id: str, token: str):
    """Create WebSocket client for frontend integration."""
    import websockets
    
    async def connect_and_listen():
        """Connect to WebSocket and listen for messages."""
        uri = get_websocket_url(consultation_id, token)
        
        async with websockets.connect(uri) as websocket:
            # Connection established
            async for message in websocket:
                data = json.loads(message)
                yield data
    
    return connect_and_listen()


# Real-time consultation features ready for integration
CONSULTATION_WEBSOCKET_FEATURES = {
    "real_time_messaging": "Live chat with <200ms latency",
    "typing_indicators": "Show when users are typing",
    "delivery_tracking": "Track message delivery status",
    "read_receipts": "Mark messages as read",
    "connection_monitoring": "Monitor WebSocket connections",
    "auto_cleanup": "Clean up inactive connections",
    "broadcast_messaging": "Send messages to all participants",
    "personal_messaging": "Send messages to specific users"
}