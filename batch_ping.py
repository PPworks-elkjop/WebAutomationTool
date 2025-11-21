"""
Batch Ping Tool - Ping multiple APs simultaneously
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict
import subprocess
import platform
import re
import concurrent.futures
import time
import socket
import struct
import select
import os
from batch_operations_base import BatchOperationWindow
from database_manager import DatabaseManager


class BatchPingWindow(BatchOperationWindow):
    """Window for batch pinging multiple APs."""
    
    def __init__(self, parent, current_user, db_manager: DatabaseManager):
        """Initialize batch ping window."""
        self.ping_count = 4
        self.timeout = 2
        self.max_parallel = 20
        
        super().__init__(parent, "Batch Ping Tool", current_user, db_manager)
    
    def _create_operation_controls(self):
        """Create ping-specific controls."""
        # Ping count
        count_frame = ttk.Frame(self.operation_frame)
        count_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(count_frame, text="Ping Count:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.ping_count_var = tk.IntVar(value=4)
        ping_count_spin = ttk.Spinbox(count_frame, from_=1, to=10, width=10,
                                     textvariable=self.ping_count_var)
        ping_count_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        # Timeout
        ttk.Label(count_frame, text="Timeout (seconds):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.timeout_var = tk.IntVar(value=2)
        timeout_spin = ttk.Spinbox(count_frame, from_=1, to=10, width=10,
                                   textvariable=self.timeout_var)
        timeout_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        # Parallel operations
        ttk.Label(count_frame, text="Max Parallel:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.parallel_var = tk.IntVar(value=20)
        parallel_spin = ttk.Spinbox(count_frame, from_=1, to=50, width=10,
                                    textvariable=self.parallel_var)
        parallel_spin.pack(side=tk.LEFT)
        
        # Help text
        help_text = ttk.Label(
            self.operation_frame,
            text="Ping multiple APs simultaneously to check connectivity. "
                 "Higher parallel count = faster but more network load.",
            foreground="gray",
            wraplength=1000
        )
        help_text.pack(anchor=tk.W, pady=(10, 0))
    
    def _get_operation_description(self) -> str:
        """Get operation description for confirmation dialog."""
        return (f"Ping all marked APs with {self.ping_count_var.get()} packets "
                f"(timeout: {self.timeout_var.get()}s, max parallel: {self.parallel_var.get()})")
    
    def _get_operation_params(self) -> dict:
        """Read tkinter variables in main thread."""
        return {
            'ping_count': self.ping_count_var.get(),
            'timeout': self.timeout_var.get(),
            'max_parallel': self.parallel_var.get()
        }
    
    def _run_operation(self, operation_params: dict = None):
        """Run batch ping operation with parallel execution and sequential pings per AP."""
        # Use parameters passed from main thread
        self.ping_count = operation_params.get('ping_count', 4)
        self.timeout = operation_params.get('timeout', 2)
        self.max_parallel = operation_params.get('max_parallel', 20)
        
        total = len(self.selected_aps)
        completed = 0
        
        # Use ThreadPoolExecutor for parallel AP processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all ping tasks (each will ping sequentially and report progress)
            future_to_ap = {
                executor.submit(self._ping_ap_sequential, ap): ap 
                for ap in self.selected_aps
            }
            
            # Process completed tasks as they finish
            for future in concurrent.futures.as_completed(future_to_ap):
                if not self.operation_running:
                    self.operation_queue.put(('log', 'Operation stopped by user', 'warning'))
                    break
                
                ap = future_to_ap[future]
                ap_id = ap['ap_id']
                
                try:
                    # Result already reported during sequential pinging
                    future.result()
                    
                except Exception as e:
                    self.operation_queue.put(('status', ap_id, 'Failed', f'Error: {str(e)}', '-'))
                    self.operation_queue.put(('log', f"{ap_id}: Error - {str(e)}", 'error'))
                
                # Update progress
                completed += 1
                progress = (completed / total) * 100
                self.operation_queue.put(('progress', progress, f"Processed {completed} of {total}"))
        
        # Operation complete
        self.operation_queue.put(('complete', None, None))
    
    def _ping_ap_sequential(self, ap: Dict):
        """Ping an AP sequentially, one ping at a time, reporting progress."""
        ap_id = ap['ap_id']
        ip = ap.get('ip_address', '')
        
        if not ip:
            self.operation_queue.put(('status', ap_id, 'Failed', 'No IP address', '0/0'))
            return
        
        successful_pings = 0
        failed_pings = 0
        ping_times = []
        
        # Ping one at a time and report progress (Windows-like: 1 second between pings)
        for i in range(1, self.ping_count + 1):
            if not self.operation_running:
                break
            
            # Update status to show current ping
            current_avg = sum(ping_times) / len(ping_times) if ping_times else 0
            status_text = f'Ping {i}/{self.ping_count}... ({current_avg:.1f}ms avg)' if ping_times else f'Ping {i}/{self.ping_count}...'
            self.operation_queue.put(('status', ap_id, 'Running', status_text, f'{i-1}/{self.ping_count}'))
            
            # Execute single ICMP ping
            ping_start = time.time()
            success, ping_time = self._send_icmp_ping(ip, self.timeout)
            ping_duration = time.time() - ping_start
            
            if success:
                successful_pings += 1
                ping_times.append(ping_time)
                # Update immediately after successful ping to show new average
                current_avg = sum(ping_times) / len(ping_times)
                self.operation_queue.put(('status', ap_id, 'Running', f'Ping {i}/{self.ping_count} OK ({current_avg:.1f}ms avg)', f'{i}/{self.ping_count}'))
            else:
                failed_pings += 1
                # Update to show failure
                current_avg = sum(ping_times) / len(ping_times) if ping_times else 0
                avg_text = f' ({current_avg:.1f}ms avg)' if ping_times else ''
                self.operation_queue.put(('status', ap_id, 'Running', f'Ping {i}/{self.ping_count} Timeout{avg_text}', f'{i}/{self.ping_count}'))
            
            # Windows-style delay: wait ~1 second between pings (or remaining time if ping took longer)
            if i < self.ping_count:  # Don't wait after last ping
                delay = max(0, 1.0 - ping_duration)
                if delay > 0:
                    time.sleep(delay)
        
        # Calculate final results
        total_sent = successful_pings + failed_pings
        if successful_pings == 0:
            # All pings failed
            self.operation_queue.put(('status', ap_id, 'Failed', 'All pings failed', f'{total_sent}/{self.ping_count}'))
            self.db.update_ap_status(ap_id, 'offline')
        else:
            # At least some pings succeeded
            loss_pct = int((failed_pings / total_sent) * 100) if total_sent > 0 else 0
            avg_time = sum(ping_times) / len(ping_times) if ping_times else 0
            
            if loss_pct == 0:
                result_text = f"Online ({avg_time:.1f}ms avg)"
                status = 'Success'
            elif loss_pct < 100:
                result_text = f"{loss_pct}% loss ({avg_time:.1f}ms avg)"
                status = 'Success'
            else:
                result_text = "100% packet loss"
                status = 'Failed'
            
            self.operation_queue.put(('status', ap_id, status, result_text, f'{total_sent}/{self.ping_count}'))
            self.operation_queue.put(('log', f"{ap_id}: {result_text}", 'success' if status == 'Success' else 'error'))
            
            if loss_pct < 100:
                self.db.update_ap_status(ap_id, 'online', avg_time)
            else:
                self.db.update_ap_status(ap_id, 'offline')
    
    def _ping_single_ap(self, ap: Dict) -> tuple[bool, str, float]:
        """
        Ping a single AP.
        
        Returns:
            tuple: (success, result_message, avg_ping_time_ms)
        """
        ip = ap.get('ip_address', '')
        
        if not ip:
            return False, "No IP address", 0.0
        
        try:
            # Determine ping command based on OS
            if platform.system().lower() == 'windows':
                # Windows ping command
                cmd = ['ping', '-n', str(self.ping_count), '-w', str(self.timeout * 1000), ip]
            else:
                # Linux/Mac ping command
                cmd = ['ping', '-c', str(self.ping_count), '-W', str(self.timeout), ip]
            
            # Execute ping
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * self.ping_count + 5
            )
            
            output = result.stdout + result.stderr
            
            # Parse ping results
            if result.returncode == 0:
                # Extract average ping time
                avg_time = self._parse_ping_time(output)
                
                # Extract packet loss
                loss = self._parse_packet_loss(output)
                
                if loss == 100:
                    return False, f"100% packet loss", 0.0
                elif loss > 0:
                    return True, f"{loss}% packet loss", avg_time
                else:
                    return True, f"Online", avg_time
            else:
                # Ping failed
                if "timed out" in output.lower() or "unreachable" in output.lower():
                    return False, "Timeout/Unreachable", 0.0
                else:
                    return False, "Ping failed", 0.0
        
        except subprocess.TimeoutExpired:
            return False, "Timeout", 0.0
        except Exception as e:
            return False, f"Error: {str(e)[:30]}", 0.0
    
    def _parse_ping_time(self, output: str) -> float:
        """Parse average ping time from ping output."""
        try:
            if platform.system().lower() == 'windows':
                # Windows format: "Average = 5ms"
                match = re.search(r'Average\s*=\s*(\d+)ms', output)
                if match:
                    return float(match.group(1))
            else:
                # Linux/Mac format: "min/avg/max = 1.234/2.345/3.456 ms"
                match = re.search(r'[\d.]+/([\d.]+)/[\d.]+', output)
                if match:
                    return float(match.group(1))
        except:
            pass
        
        return 0.0
    
    def _parse_packet_loss(self, output: str) -> int:
        """Parse packet loss percentage from ping output."""
        try:
            # Look for "X% loss" or "(X% loss)"
            match = re.search(r'(\d+)%\s+(?:packet\s+)?loss', output, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except:
            pass
        
        return 0
    
    def _send_icmp_ping(self, host: str, timeout: float) -> tuple[bool, float]:
        """
        Send a single ICMP echo request and wait for reply.
        
        Returns:
            tuple: (success, round_trip_time_ms)
        """
        try:
            # Try to resolve hostname to IP
            try:
                dest_addr = socket.gethostbyname(host)
            except socket.gaierror:
                return False, 0.0
            
            # Create raw ICMP socket (requires admin/root on some systems)
            # If that fails, fall back to subprocess
            try:
                icmp = socket.getprotobyname("icmp")
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
                sock.settimeout(timeout)
            except (PermissionError, OSError):
                # Fall back to subprocess ping
                return self._fallback_ping(host, timeout)
            
            # ICMP Echo Request packet
            packet_id = os.getpid() & 0xFFFF
            seq_number = 1
            
            # Create ICMP header (type=8 for echo request, code=0)
            checksum = 0
            header = struct.pack('!BBHHH', 8, 0, checksum, packet_id, seq_number)
            data = struct.pack('!d', time.time())  # Timestamp
            
            # Calculate checksum
            checksum = self._calculate_checksum(header + data)
            header = struct.pack('!BBHHH', 8, 0, checksum, packet_id, seq_number)
            
            packet = header + data
            
            # Send packet
            send_time = time.time()
            sock.sendto(packet, (dest_addr, 0))
            
            # Wait for reply
            try:
                ready = select.select([sock], [], [], timeout)
                if ready[0]:
                    recv_packet, addr = sock.recvfrom(1024)
                    recv_time = time.time()
                    
                    # Extract ICMP header from IP packet (skip 20-byte IP header)
                    icmp_header = recv_packet[20:28]
                    type, code, checksum, p_id, sequence = struct.unpack('!BBHHH', icmp_header)
                    
                    # Check if this is our echo reply (type=0) and ID matches
                    if type == 0 and p_id == packet_id:
                        rtt = (recv_time - send_time) * 1000  # Convert to ms
                        sock.close()
                        return True, rtt
                    
                sock.close()
                return False, 0.0
                
            except socket.timeout:
                sock.close()
                return False, 0.0
                
        except Exception:
            return False, 0.0
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate ICMP checksum."""
        sum = 0
        count_to = (len(data) // 2) * 2
        
        for i in range(0, count_to, 2):
            sum += (data[i + 1] << 8) + data[i]
        
        if count_to < len(data):
            sum += data[-1]
        
        sum = (sum >> 16) + (sum & 0xFFFF)
        sum += (sum >> 16)
        
        return ~sum & 0xFFFF
    
    def _fallback_ping(self, host: str, timeout: float) -> tuple[bool, float]:
        """Fallback to subprocess ping if raw sockets not available."""
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), host]
            else:
                cmd = ['ping', '-c', '1', '-W', str(int(timeout)), host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 1)
            rtt = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # Try to parse actual RTT from output
                parsed_time = self._parse_ping_time(result.stdout + result.stderr)
                if parsed_time > 0:
                    return True, parsed_time
                return True, rtt
            
            return False, 0.0
            
        except Exception:
            return False, 0.0


def main():
    """Test the batch ping window."""
    root = tk.Tk()
    root.withdraw()
    
    from database_manager import DatabaseManager
    db = DatabaseManager()
    
    window = BatchPingWindow(None, "test_user", db)
    window.window.mainloop()


if __name__ == '__main__':
    main()
