"""
Process Manager

Handles process execution, shell commands, and screen sessions.
"""

import subprocess
import logging
from typing import Optional, Tuple, Dict, Any


class ProcessManager:
    """Manages process execution and shell operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_timeout = 10
    
    def execute_command(self, command: str, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Execute a shell command and return success status and output.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds (default: 10)
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        timeout = timeout or self.default_timeout
        
        try:
            self.logger.info(f"Executing command: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            output = result.stdout.strip() or result.stderr.strip() or "(No output)"
            
            # Limit output length for messaging platforms
            if len(output) > 4000:
                output = output[:4000] + "... (truncated)"
            
            success = result.returncode == 0
            if not success:
                self.logger.warning(f"Command failed with return code {result.returncode}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def ensure_screen_session(self, session_name: str = "p42r_session") -> bool:
        """
        Ensure a screen session exists, create if it doesn't.
        
        Args:
            session_name: Name of the screen session
            
        Returns:
            True if session exists or was created successfully
        """
        try:
            # Check if session exists
            result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
            
            if session_name not in result.stdout:
                # Create new session
                subprocess.run(["screen", "-dmS", session_name])
                self.logger.info(f"Created screen session: {session_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error managing screen session: {e}")
            return False
    
    def send_to_screen(self, command: str, session_name: str = "p42r_session") -> bool:
        """
        Send a command to a screen session.
        
        Args:
            command: Command to send
            session_name: Target screen session name
            
        Returns:
            True if command was sent successfully
        """
        try:
            if not self.ensure_screen_session(session_name):
                return False
            
            # Send command to screen session
            screen_cmd = f'screen -S {session_name} -X stuff "{command}\\n"'
            subprocess.run(screen_cmd, shell=True, check=True)
            
            self.logger.info(f"Sent to screen '{session_name}': {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending to screen: {e}")
            return False
    
    def list_processes(self, filter_term: Optional[str] = None) -> str:
        """
        List running processes, optionally filtered.
        
        Args:
            filter_term: Optional term to filter processes
            
        Returns:
            Process list as string
        """
        try:
            cmd = "ps aux"
            if filter_term:
                cmd += f" | grep {filter_term}"
            
            success, output = self.execute_command(cmd)
            return output if success else "Failed to list processes"
            
        except Exception as e:
            self.logger.error(f"Error listing processes: {e}")
            return f"Error: {e}"
    
    def kill_process(self, pid_or_name: str) -> Tuple[bool, str]:
        """
        Kill a process by PID or name.
        
        Args:
            pid_or_name: Process ID or process name
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try as PID first
            if pid_or_name.isdigit():
                cmd = f"kill {pid_or_name}"
            else:
                cmd = f"pkill {pid_or_name}"
            
            return self.execute_command(cmd)
            
        except Exception as e:
            error_msg = f"Error killing process: {e}"
            self.logger.error(error_msg)
            return False, error_msg
