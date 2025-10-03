"""
Security Manager

Handles authentication, password management, and security operations.
"""

import logging
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class SecurityManager:
    """Manages security and authentication operations."""
    
    def __init__(self, log_key: str = "", xor_key: int = 42):
        self.logger = logging.getLogger(__name__)
        self.log_key = log_key
        self.xor_key = xor_key
        self.authorized_chats: Dict[str, Any] = {}
        self.bot_start_time = datetime.now(timezone.utc)
    
    def decode_password(self, xor_key: Optional[int] = None) -> Optional[str]:
        """
        Decode password from XOR-encoded hex string.
        
        Args:
            xor_key: XOR key to use for decoding (uses instance default if None)
            
        Returns:
            Decoded password string, or None if decoding fails
        """
        if not self.log_key:
            self.logger.warning("No LOG_KEY configured")
            return None
        
        xor_key = xor_key or self.xor_key
        
        try:
            xored_bytes = bytes.fromhex(self.log_key)
            password = ''.join(chr(b ^ xor_key) for b in xored_bytes)
            self.logger.debug("Password decoded successfully")
            return password
            
        except Exception as e:
            self.logger.error(f"Error decoding password: {e}")
            return None
    
    def encode_password(self, password: str, xor_key: Optional[int] = None) -> str:
        """
        Encode password to XOR-encoded hex string.
        
        Args:
            password: Plain text password to encode
            xor_key: XOR key to use for encoding (uses instance default if None)
            
        Returns:
            Hex-encoded XOR string
        """
        xor_key = xor_key or self.xor_key
        
        try:
            xored_bytes = bytes([ord(c) ^ xor_key for c in password])
            hex_string = xored_bytes.hex()
            self.logger.debug("Password encoded successfully")
            return hex_string
            
        except Exception as e:
            self.logger.error(f"Error encoding password: {e}")
            return ""
    
    def type_password_with_xdotool(self, password: Optional[str] = None) -> bool:
        """
        Type password using xdotool (clears field first).
        
        Args:
            password: Password to type (decodes from LOG_KEY if None)
            
        Returns:
            True if successful, False otherwise
        """
        if password is None:
            password = self.decode_password()
        
        if not password:
            self.logger.error("No password available to type")
            return False
        
        try:
            # Clear the field
            subprocess.run(["xdotool", "key", "--repeat", "50", "BackSpace"], check=True)
            
            # Type the password
            subprocess.run(["xdotool", "type", password], check=True)
            
            # Press Enter
            subprocess.run(["xdotool", "key", "Return"], check=True)
            
            self.logger.info("Password typed successfully with xdotool")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"xdotool command failed: {e}")
            return False
        except FileNotFoundError:
            self.logger.error("xdotool not found - please install it")
            return False
        except Exception as e:
            self.logger.error(f"Error typing password: {e}")
            return False
    
    def is_chat_authorized(self, chat_id: str, authorized_chat_id: str) -> bool:
        """
        Check if a chat ID is authorized.
        
        Args:
            chat_id: Chat ID to check
            authorized_chat_id: The authorized chat ID
            
        Returns:
            True if authorized, False otherwise
        """
        is_authorized = str(chat_id) == str(authorized_chat_id)
        
        if not is_authorized:
            self.logger.warning(f"Unauthorized access attempt from chat ID: {chat_id}")
        
        return is_authorized
    
    def is_message_recent(self, message_time: datetime) -> bool:
        """
        Check if a message was sent after the bot started (prevent old message processing).
        
        Args:
            message_time: UTC datetime when message was sent
            
        Returns:
            True if message is recent, False if it's old
        """
        is_recent = message_time >= self.bot_start_time
        
        if not is_recent:
            self.logger.info(f"Ignoring old message from {message_time}")
        
        return is_recent
    
    def add_authorized_chat(self, chat_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a chat ID to the authorized list.
        
        Args:
            chat_id: Chat ID to authorize
            metadata: Optional metadata about the chat
        """
        self.authorized_chats[str(chat_id)] = {
            'added_at': datetime.now(timezone.utc),
            'metadata': metadata or {}
        }
        self.logger.info(f"Added authorized chat: {chat_id}")
    
    def remove_authorized_chat(self, chat_id: str) -> bool:
        """
        Remove a chat ID from the authorized list.
        
        Args:
            chat_id: Chat ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if str(chat_id) in self.authorized_chats:
            del self.authorized_chats[str(chat_id)]
            self.logger.info(f"Removed authorized chat: {chat_id}")
            return True
        return False
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and configuration."""
        return {
            'bot_start_time': self.bot_start_time.isoformat(),
            'authorized_chats_count': len(self.authorized_chats),
            'password_configured': bool(self.log_key),
            'xor_key_set': bool(self.xor_key)
        }
