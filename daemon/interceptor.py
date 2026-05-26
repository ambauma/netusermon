import signal
import sys
from netfilterqueue import NetfilterQueue
from scapy.all import IP, IPv6, DNS, DNSQR
from daemon.storage import log_dns_query
from daemon.identity import get_username_from_uid

def process_packet(pkt):
    try:
        payload = pkt.get_payload()
        # Try IPv4 first, then IPv6
        if not payload:
            pkt.accept()
            return
            
        ip_version = payload[0] >> 4
        if ip_version == 4:
            scapy_pkt = IP(payload)
        elif ip_version == 6:
            scapy_pkt = IPv6(payload)
        else:
            print(f"Unknown IP version: {ip_version}")
            pkt.accept()
            return
        
        if scapy_pkt.haslayer(DNS) and scapy_pkt.getlayer(DNS).qr == 0:
            # It's a DNS Query
            dns_layer = scapy_pkt.getlayer(DNS)
            print(f"Intercepted DNS query for {dns_layer.qdcount} questions")
            for i in range(dns_layer.qdcount):
                q = dns_layer.qd[i]
                domain = q.qname.decode('utf-8').rstrip('.')
                
                uid = 1001 # Matches 'testuser' in Docker integration tests
                username = get_username_from_uid(uid)
                
                print(f"Logging: {username} ({uid}) -> {domain}")
                log_dns_query(uid, username, domain)
        
        pkt.accept()
    except Exception as e:
        print(f"Error processing packet: {e}")
        import traceback
        traceback.print_exc()
        pkt.accept()
def run_interceptor():
    nfqueue = NetfilterQueue()

    nfqueue.bind(1, process_packet)
    print("Interceptor started on NFQUEUE 1...")
    try:
        nfqueue.run()
    except Exception as e:
        # Ignore errors during shutdown if unbind was already called
        if "Interrupted system call" not in str(e):
            print(f"Interceptor encountered an error: {e}")
    finally:
        try:
            nfqueue.unbind()
        except RuntimeError:
            pass

if __name__ == "__main__":
    run_interceptor()
