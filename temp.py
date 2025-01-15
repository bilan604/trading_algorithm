import socket

# Get the local machine name
hostname = socket.gethostname()

# Get the local IPv4 address
ipv4_address = socket.gethostbyname(hostname)

# Get the local IPv6 address (may not always be available)
try:
    ipv6_address = socket.getaddrinfo(hostname, None, socket.AF_INET6)[0][4][0]
except IndexError:
    ipv6_address = "IPv6 address not found"

print(f"IPv4 Address: {ipv4_address}")
print(f"IPv6 Address: {ipv6_address}")
