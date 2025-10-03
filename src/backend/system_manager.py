"""
System Manager

Handles general system operations like locking, shutdown, restart.
"""

import os
import sys
import subprocess
import logging
from typing import Optional
from datetime import datetime


class SystemManager:
    """Manages system-level operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def shutdown_system(self) -> None:
        """Shutdown the p42r application gracefully."""
        self.logger.info("p42r application shutdown requested")
        
        # Clean up PID file if it exists
        import os
        pid_file = "/tmp/p42r.pid"
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
                self.logger.info("Cleaned up PID file")
            except Exception as e:
                self.logger.error(f"Failed to clean PID file: {e}")
        
        # Graceful shutdown
        sys.exit(0)
    
    def restart_application(self, script_path: Optional[str] = None) -> None:
        """Restart the p42r application."""
        self.logger.info("p42r application restart requested")
        
        # For daemon mode, we need to handle restart differently
        import os
        pid_file = "/tmp/p42r.pid"
        
        if os.path.exists(pid_file):
            # Running as daemon - restart via script
            restart_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "..", "..", "start_p42r_daemon.sh")
            if os.path.exists(restart_script):
                os.system(f"nohup {restart_script} &")
                sys.exit(0)
        
        # Fallback to direct restart
        if script_path:
            os.chdir(os.path.dirname(script_path))
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def get_system_info(self) -> dict:
        """Get basic system information."""
        try:
            import platform
            return {
                'platform': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
