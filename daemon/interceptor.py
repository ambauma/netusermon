import signal
import sys
from netfilterqueue import NetfilterQueue
from scapy.all import IP, DNS, DNSQR
from daemon.storage import log_dns_query, init_db
from daemon.identity import get_username_from_uid

def process_packet(pkt):
    try:
        payload = pkt.get_payload()
        scapy_pkt = IP(payload)
        
        if scapy_pkt.haslayer(DNS) and scapy_pkt.getlayer(DNS).qr == 0:
            # It's a DNS Query
            dns_layer = scapy_pkt.getlayer(DNS)
            for i in range(dns_layer.qdcount):
                q = dns_layer.qd[i]
                domain = q.qname.decode('utf-8').rstrip('.')
                
                # In a real scenario, we'd use something like 'ss' or '/proc/net' 
                # to find the UID of the socket. For now, we assume the packet 
                # metadata or nfqueue might provide it if configured correctly, 
                # but often we need to correlate via mark or conntrack.
                # NFQUEUE doesn't directly give UID. 
                # We'll use a placeholder or system-wide mapping for this initial draft.
                uid = 1000 # Placeholder for demo; real implementation needs socket correlation
                username = get_username_from_uid(uid)
                
                print(f"Logging: {username} ({uid}) -> {domain}")
                log_dns_query(uid, username, domain)
                
        pkt.accept()
    except Exception as e:
        print(f"Error processing packet: {e}")
        pkt.accept()

def run_interceptor():
    init_db()
    nfqueue = NetfilterQueue()
    nfqueue.bind(1, process_packet)
    print("Interceptor started on NFQUEUE 1...")
    try:
        nfqueue.run()
    except KeyboardInterrupt:
        print("Stopping interceptor...")
    finally:
        nfqueue.unbind()

if __name__ == "__main__":
    run_interceptor()
