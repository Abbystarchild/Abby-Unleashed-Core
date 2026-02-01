"""
Generate self-signed SSL certificate for HTTPS support.
Required for mobile camera access over local network.
"""
import os
import subprocess
import sys
from pathlib import Path


def generate_ssl_cert(cert_dir: str = "ssl"):
    """Generate a self-signed SSL certificate using OpenSSL or Python."""
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    cert_file = cert_path / "cert.pem"
    key_file = cert_path / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print(f"✅ SSL certificates already exist in {cert_dir}/")
        return str(cert_file), str(key_file)
    
    print("🔐 Generating self-signed SSL certificate...")
    
    # Try using cryptography library (pure Python)
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        import ipaddress
        import socket
        
        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Get local IP addresses for SAN
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Build certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Network"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Abby Unleashed"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Abby Local Server"),
        ])
        
        # Add Subject Alternative Names for local access
        san_list = [
            x509.DNSName("localhost"),
            x509.DNSName(hostname),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        
        # Try to add local network IP
        try:
            san_list.append(x509.IPAddress(ipaddress.IPv4Address(local_ip)))
        except:
            pass
        
        # Add common local network ranges
        for i in range(1, 255):
            try:
                san_list.append(x509.IPAddress(ipaddress.IPv4Address(f"192.168.1.{i}")))
                san_list.append(x509.IPAddress(ipaddress.IPv4Address(f"192.168.0.{i}")))
                san_list.append(x509.IPAddress(ipaddress.IPv4Address(f"192.168.254.{i}")))
            except:
                break  # Stop if we hit issues
            if i > 50:  # Limit to avoid huge cert
                break
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )
        
        # Write key
        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Write cert
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"✅ SSL certificate generated!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        print(f"   Valid for: 365 days")
        print(f"   Local IP: {local_ip}")
        print()
        print("⚠️  NOTE: Your browser will show a security warning for self-signed certs.")
        print("   Click 'Advanced' → 'Proceed anyway' to accept it.")
        
        return str(cert_file), str(key_file)
        
    except ImportError:
        print("❌ cryptography library not installed.")
        print("   Install with: pip install cryptography")
        print()
        print("   Or generate manually with OpenSSL:")
        print(f"   openssl req -x509 -newkey rsa:2048 -keyout {key_file} -out {cert_file} -days 365 -nodes")
        return None, None


if __name__ == "__main__":
    cert, key = generate_ssl_cert()
    if cert and key:
        print()
        print("🚀 Now start the server with HTTPS:")
        print("   python api_server.py --https")
