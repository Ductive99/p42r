"""
Base Adapter

Abstract base class for platform adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Awaitable
import logging


class BaseAdapter(ABC):
    """Abstract base class for platform adapters."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.message_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
        self.is_running = False
    
    def set_message_handler(self, handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]) -> None:
        """
        Set the message handler function.
        
        Args:
            handler: Async function that takes (message_text, context) and returns response dict
        """
        self.message_handler = handler
    
    @abstractmethod
    async def start(self) -> None:
        """Start the adapter (connect to platform, begin listening, etc.)."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the adapter gracefully."""
        pass
    
    @abstractmethod
    async def send_text_message(self, text: str, context: Dict[str, Any]) -> bool:
        """
        Send a text message back to the platform.
        
        Args:
            text: Message text to send
            context: Platform-specific context (chat_id, user_id, etc.)
            
        Returns:
            True if message was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_image_message(self, image_path: str, caption: str, context: Dict[str, Any]) -> bool:
        """
        Send an image message back to the platform.
        
        Args:
            image_path: Path to image file
            caption: Image caption text
            context: Platform-specific context
            
        Returns:
            True if image was sent successfully
        """
        pass
    
    @abstractmethod
    def is_authorized(self, context: Dict[str, Any]) -> bool:
        """
        Check if the message sender is authorized.
        
        Args:
            context: Platform-specific context
            
        Returns:
            True if authorized
        """
        pass
    
    @abstractmethod
    def extract_message_info(self, platform_message: Any) -> Dict[str, Any]:
        """
        Extract message information from platform-specific message object.
        
        Args:
            platform_message: Platform's message object
            
        Returns:
            Standardized message info dict
        """
        pass
    
    async def handle_platform_message(self, platform_message: Any) -> None:
        """
        Handle an incoming message from the platform.
        
        Args:
            platform_message: Platform's message object
        """
        try:
            # Extract message info
            message_info = self.extract_message_info(platform_message)
            
            # Check authorization
            if not self.is_authorized(message_info):
                await self.send_text_message("Unauthorized access.", message_info)
                return
            
            # Get message text
            text = message_info.get('text', '').strip()
            if not text:
                return
            
            # Call message handler if set
            if self.message_handler:
                response = await self.message_handler(text, message_info)
                await self.handle_response(response, message_info)
            else:
                self.logger.warning("No message handler set")
                
        except Exception as e:
            self.logger.error(f"Error handling platform message: {e}")
            try:
                message_info = self.extract_message_info(platform_message)
                await self.send_text_message(f"Error processing message: {e}", message_info)
            except:
                pass  # Best effort error reporting
    
    async def handle_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Handle a response from the command system.
        
        Args:
            response: Response dictionary from command handler
            context: Message context
        """
        try:
            message = response.get('message', 'No message')
            success = response.get('success', False)
            data = response.get('data', {})
            
            # Send text response
            await self.send_text_message(message, context)
            
            # Handle image data if present
            if 'image_path' in data:
                image_path = data['image_path']
                caption = f"📸 {message}" if success else f"❌ {message}"
                await self.send_image_message(image_path, caption, context)
                
                # Clean up temporary files
                try:
                    import os
                    if os.path.exists(image_path) and '/tmp/' in image_path:
                        os.remove(image_path)
                except Exception as e:
                    self.logger.warning(f"Could not clean up temp file {image_path}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get adapter information."""
        return {
            'name': self.name,
            'class': self.__class__.__name__,
            'running': self.is_running,
            'has_handler': self.message_handler is not None
        }
