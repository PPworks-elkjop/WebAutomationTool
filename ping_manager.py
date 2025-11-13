"""
Ping Manager - Handles continuous ping operations for APs
"""
import threading
import time


class PingManager:
    """Manages continuous ping operations for multiple APs"""
    
    def __init__(self, ping_host_func):
        """
        Initialize the ping manager
        
        Args:
            ping_host_func: Function to ping a host (should take ip_address, timeout as args)
        """
        self.ping_host_func = ping_host_func
        self.ping_threads = {}
        self.ping_stop_flags = {}
        self.ping_counters = {}
        
    def start_ping(self, item_id, ip_address, update_callback):
        """
        Start continuous ping for an AP
        
        Args:
            item_id: Unique identifier for the AP
            ip_address: IP address to ping
            update_callback: Function to call with ping results (response_time_ms, count)
        """
        if item_id in self.ping_threads and self.ping_threads[item_id].is_alive():
            return  # Already pinging
        
        # Initialize stop flag and counter
        self.ping_stop_flags[item_id] = False
        self.ping_counters[item_id] = 0
        
        # Create and start ping thread
        thread = threading.Thread(
            target=self._ping_loop,
            args=(item_id, ip_address, update_callback),
            daemon=True
        )
        self.ping_threads[item_id] = thread
        thread.start()
    
    def stop_ping(self, item_id):
        """
        Stop continuous ping for an AP
        
        Args:
            item_id: Unique identifier for the AP
        """
        if item_id in self.ping_stop_flags:
            self.ping_stop_flags[item_id] = True
    
    def stop_all(self):
        """Stop all active ping operations"""
        for item_id in list(self.ping_stop_flags.keys()):
            self.ping_stop_flags[item_id] = True
        
        # Wait for threads to finish (with timeout)
        for thread in self.ping_threads.values():
            if thread.is_alive():
                thread.join(timeout=2)
    
    def is_pinging(self, item_id):
        """
        Check if an AP is currently being pinged
        
        Args:
            item_id: Unique identifier for the AP
            
        Returns:
            bool: True if pinging is active
        """
        return (item_id in self.ping_threads and 
                self.ping_threads[item_id].is_alive() and
                not self.ping_stop_flags.get(item_id, False))
    
    def get_ping_count(self, item_id):
        """
        Get the current ping count for an AP
        
        Args:
            item_id: Unique identifier for the AP
            
        Returns:
            int: Number of pings sent
        """
        return self.ping_counters.get(item_id, 0)
    
    def _ping_loop(self, item_id, ip_address, update_callback):
        """
        Internal loop that continuously pings an IP
        
        Args:
            item_id: Unique identifier for the AP
            ip_address: IP address to ping
            update_callback: Function to call with ping results
        """
        while not self.ping_stop_flags.get(item_id, False):
            try:
                # Ping the host (returns tuple: (success, response_time))
                result = self.ping_host_func(ip_address, timeout=1)
                
                # Handle tuple response (success, response_time)
                if isinstance(result, tuple):
                    success, response_time = result
                else:
                    # Fallback if function returns single value
                    success = result is not None
                    response_time = result
                
                # Increment counter
                self.ping_counters[item_id] = self.ping_counters.get(item_id, 0) + 1
                
                # Format result text
                if success and response_time is not None:
                    # response_time is already in ms from ping_host
                    result_text = f"{response_time} ms"
                else:
                    result_text = "Timeout"
                
                # Call the update callback
                update_callback(result_text, self.ping_counters[item_id])
                
                # Wait 1 second before next ping
                time.sleep(1)
                
            except Exception as e:
                update_callback(f"Error: {str(e)}", self.ping_counters.get(item_id, 0))
                time.sleep(1)
        
        # Clean up when stopped
        if item_id in self.ping_counters:
            del self.ping_counters[item_id]
