"""
Telegram Adapter

Telegram bot platform adapter for p42r.
"""

import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from .base_adapter import BaseAdapter


class TelegramAdapter(BaseAdapter):
    """Telegram platform adapter."""
    
    def __init__(self, bot_token: str, authorized_chat_id: str):
        super().__init__("telegram")
        self.bot_token = bot_token
        self.authorized_chat_id = str(authorized_chat_id)
        self.application = None
        self.bot_start_time = datetime.now(timezone.utc)
    
    async def start(self) -> None:
        """Start the Telegram bot."""
        try:
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("help", self._handle_help_command))
            self.application.add_handler(CommandHandler("start", self._handle_start_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
            self.application.add_handler(MessageHandler(filters.COMMAND, self._handle_command_message))
            
            self.logger.info("Starting Telegram bot...")
            
            # Initialize the application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling in the background
            if self.application.updater:
                await self.application.updater.start_polling(drop_pending_updates=True)
            
            self.is_running = True
            self.logger.info("Telegram bot started successfully")
            
        except ImportError:
            self.logger.error("python-telegram-bot not installed. Please install it with: pip install python-telegram-bot")
            raise
        except Exception as e:
            self.logger.error(f"Error starting Telegram adapter: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the Telegram bot."""
        try:
            if self.application and self.is_running:
                # Stop polling
                if self.application.updater:
                    await self.application.updater.stop()
                
                # Stop and shutdown application
                await self.application.stop()
                await self.application.shutdown()
                
                self.is_running = False
                self.logger.info("Telegram bot stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Telegram adapter: {e}")
    
    async def send_text_message(self, text: str, context: Dict[str, Any]) -> bool:
        """Send a text message via Telegram."""
        try:
            if not self.application or not self.application.bot:
                self.logger.error("Telegram bot not initialized")
                return False
            
            chat_id = context.get('chat_id')
            if not chat_id:
                self.logger.error("No chat_id in context")
                return False
            
            await self.application.bot.send_message(chat_id=chat_id, text=text)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending text message: {e}")
            return False
    
    async def send_image_message(self, image_path: str, caption: str, context: Dict[str, Any]) -> bool:
        """Send an image message via Telegram."""
        try:
            if not self.application or not self.application.bot:
                self.logger.error("Telegram bot not initialized")
                return False
            
            chat_id = context.get('chat_id')
            if not chat_id:
                self.logger.error("No chat_id in context")
                return False
            
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return False
            
            with open(image_path, 'rb') as image_file:
                await self.application.bot.send_photo(
                    chat_id=chat_id,
                    photo=image_file,
                    caption=caption
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending image message: {e}")
            return False
    
    def is_authorized(self, context: Dict[str, Any]) -> bool:
        """Check if the message sender is authorized."""
        chat_id = str(context.get('chat_id', ''))
        return chat_id == self.authorized_chat_id
    
    def extract_message_info(self, platform_message: Any) -> Dict[str, Any]:
        """Extract message information from Telegram update."""
        try:
            update = platform_message
            message = update.message
            
            info = {
                'chat_id': str(update.effective_chat.id),
                'user_id': str(update.effective_user.id) if update.effective_user else None,
                'username': update.effective_user.username if update.effective_user else None,
                'text': message.text or '',
                'message_id': message.message_id,
                'date': message.date,
                'is_recent': self._is_message_recent(message.date)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting message info: {e}")
            return {
                'chat_id': 'unknown',
                'text': '',
                'is_recent': False
            }
    
    def _is_message_recent(self, message_date: datetime) -> bool:
        """Check if message was sent after bot started."""
        return message_date >= self.bot_start_time
    
    async def _handle_help_command(self, update, context):
        """Handle /help command."""
        if not self.is_authorized(self.extract_message_info(update)):
            await update.message.reply_text("Unauthorized.")
            return
        
        help_text = """
🤖 **p42r - Remote Control Bot**

Available commands:
• `/help` - Show this help message
• `/login` or `/log` - Type configured password
• `/lock` - Lock the screen
• `/restart` - Restart the bot
• `/kill` - Shutdown the bot
• `/pic` - Take webcam photo
• `/screenshot` - Take screenshot
• `/run <command>` - Execute shell command
• `/run_screen <command>` - Send command to screen session
• `/ps [filter]` - List processes
• `/info` - Show system information

For more detailed help, use: `/help <command>`
        """
        await update.message.reply_text(help_text)
    
    async def _handle_start_command(self, update, context):
        """Handle /start command."""
        if not self.is_authorized(self.extract_message_info(update)):
            await update.message.reply_text("Unauthorized.")
            return
        
        welcome_text = """
🚀 **Welcome to p42r!**

Your remote control bot is ready. Use `/help` to see available commands.
        """
        await update.message.reply_text(welcome_text)
    
    async def _handle_text_message(self, update, context):
        """Handle regular text messages."""
        await self.handle_platform_message(update)
    
    async def _handle_command_message(self, update, context):
        """Handle command messages."""
        message_info = self.extract_message_info(update)
        
        # Check authorization
        if not self.is_authorized(message_info):
            await update.message.reply_text("Unauthorized.")
            return
        
        # Check if message is recent
        if not message_info.get('is_recent', False):
            await update.message.reply_text("Ignoring old message (sent before bot started).")
            return
        
        await self.handle_platform_message(update)
