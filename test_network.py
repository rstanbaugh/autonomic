#!/usr/bin/env python3
"""Test network connectivity to Mirage server."""
import socket
import sys

print("[*] Testing network connectivity...")

try:
    print("[*] Resolving 192.168.0.219:5004...")
    addresses = socket.getaddrinfo('192.168.0.219', 5004, socket.AF_INET, socket.SOCK_STREAM)
    print(f"[+] getaddrinfo: {addresses[0]}")
    
    family, socktype, proto, canonname, sockaddr = addresses[0]
    print(f"[*] Creating socket...")
    s = socket.socket(family, socktype, proto)
    
    print(f"[*] Connecting to {sockaddr}...")
    result = s.connect_ex(sockaddr)
    print(f"[+] connect_ex result: {result}")
    
    if result == 0:
        print("[+] Connected! Sending handshake...")
        s.sendall(b'SetClientType Core3Player\r\n')
        response = s.recv(1024)
        print(f"[+] Response: {response}")
        s.close()
        print("[+] SUCCESS")
        sys.exit(0)
    else:
        import errno
        print(f"[-] Error {result}: {errno.errorcode.get(result, 'UNKNOWN')}")
        s.close()
        sys.exit(1)
        
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"[-] Error: {e}")
    sys.exit(1)
