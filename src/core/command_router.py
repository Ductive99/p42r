"""
Command Router

Routes user commands to appropriate handlers.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from ..handlers.base_handler import BaseHandler


class CommandRouter:
    """Routes commands to appropriate handlers."""
    
    def __init__(self):
        self.handlers: Dict[str, BaseHandler] = {}
        self.command_map: Dict[str, str] = {}  # command -> handler_name
        self.logger = logging.getLogger(__name__)
    
    def register_handler(self, handler: BaseHandler) -> None:
        """
        Register a command handler.
        
        Args:
            handler: Handler instance to register
        """
        handler_name = handler.name
        self.handlers[handler_name] = handler
        
        # Map all supported commands to this handler
        for command in handler.get_supported_commands():
            if command in self.command_map:
                self.logger.warning(f"Command '{command}' already mapped to handler '{self.command_map[command]}', overriding with '{handler_name}'")
            
            self.command_map[command] = handler_name
        
        self.logger.info(f"Registered handler '{handler_name}' with commands: {handler.get_supported_commands()}")
    
    def unregister_handler(self, handler_name: str) -> bool:
        """
        Unregister a command handler.
        
        Args:
            handler_name: Name of handler to unregister
            
        Returns:
            True if handler was found and removed
        """
        if handler_name not in self.handlers:
            return False
        
        handler = self.handlers[handler_name]
        
        # Remove command mappings
        commands_to_remove = []
        for command, mapped_handler in self.command_map.items():
            if mapped_handler == handler_name:
                commands_to_remove.append(command)
        
        for command in commands_to_remove:
            del self.command_map[command]
        
        # Remove handler
        del self.handlers[handler_name]
        
        self.logger.info(f"Unregistered handler '{handler_name}'")
        return True
    
    def parse_command(self, text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Parse command text into command name and arguments.
        
        Args:
            text: Raw command text (e.g., "/run ls -la")
            
        Returns:
            Tuple of (command_name, args_dict)
        """
        text = text.strip()
        
        # Remove leading slash if present
        if text.startswith('/'):
            text = text[1:]
        
        if not text:
            return "", None
        
        parts = text.split()
        command = parts[0].lower()
        
        if len(parts) == 1:
            return command, None
        
        # For commands that take a single argument string (like run, run_screen)
        if command in ['run', 'exec', 'run_screen']:
            args = {
                'command': ' '.join(parts[1:])
            }
        # For commands that take specific parameters
        elif command in ['kill']:
            args = {
                'target': parts[1] if len(parts) > 1 else None
            }
        elif command in ['ps', 'list'] and len(parts) > 1:
            args = {
                'filter': parts[1]
            }
        elif command == 'set_password' and len(parts) > 1:
            args = {
                'password': parts[1],
                'xor_key': int(parts[2]) if len(parts) > 2 else None
            }
        elif command == 'log' and len(parts) > 1:
            args = {
                'api_key': parts[1]
            }
        elif command == 'cleanup' and len(parts) > 1:
            try:
                args = {
                    'max_age_hours': int(parts[1])
                }
            except ValueError:
                args = None
        else:
            # Generic argument parsing for other commands
            args = {}
            for i in range(1, len(parts)):
                args[f'arg{i}'] = parts[i]
            
            if not args:
                args = None
        
        return command, args
    
    async def route_command(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a command to the appropriate handler.
        
        Args:
            text: Command text to route
            context: Optional context from platform adapter
            
        Returns:
            Response dictionary from handler
        """
        try:
            command, args = self.parse_command(text)
            
            if not command:
                return self._create_error_response("Empty command")
            
            # Add context to args if provided
            if args is None:
                args = {}
            if context:
                args['_context'] = context
            
            # Find handler for command
            if command not in self.command_map:
                return self._create_error_response(f"Unknown command: {command}")
            
            handler_name = self.command_map[command]
            handler = self.handlers[handler_name]
            
            self.logger.info(f"Routing command '{command}' to handler '{handler_name}'")
            
            # Execute command
            response = await handler.handle(command, args)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error routing command '{text}': {e}")
            return self._create_error_response(f"Routing error: {e}")
    
    def get_help(self, command: Optional[str] = None) -> str:
        """
        Get help information for commands.
        
        Args:
            command: Specific command to get help for (None for all)
            
        Returns:
            Help text string
        """
        if command:
            if command not in self.command_map:
                return f"Unknown command: {command}"
            
            handler_name = self.command_map[command]
            handler = self.handlers[handler_name]
            return handler.get_help(command)
        
        # Get help for all commands
        help_sections = []
        
        for handler_name, handler in self.handlers.items():
            section = f"\n**{handler_name.title()} Commands:**\n"
            section += handler.get_help()
            help_sections.append(section)
        
        return "\n".join(help_sections)
    
    def get_available_commands(self) -> List[str]:
        """Get list of all available commands."""
        return sorted(list(self.command_map.keys()))
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about registered handlers."""
        info = {}
        for handler_name, handler in self.handlers.items():
            info[handler_name] = {
                'commands': handler.get_supported_commands(),
                'class': handler.__class__.__name__
            }
        return info
    
    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            'success': False,
            'message': message,
            'handler': 'router'
        }
