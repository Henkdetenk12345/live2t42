#!/usr/bin/env python3
"""
Live Digtal Teletext to T42 converter
Direct combination of @ZXGuesser ts2pes.py and pes2t42.py
"""

import sys
import requests

# Bit reversal lookup table
REVERSE_BYTES = [0x00, 0x80, 0x40, 0xC0, 0x20, 0xA0, 0x60, 0xE0, 0x10, 0x90, 0x50, 0xD0, 0x30, 0xB0, 0x70, 0xF0, 0x08, 0x88, 0x48, 0xC8, 0x28, 0xA8, 0x68, 0xE8, 0x18, 0x98, 0x58, 0xD8, 0x38, 0xB8, 0x78, 0xF8, 0x04, 0x84, 0x44, 0xC4, 0x24, 0xA4, 0x64, 0xE4, 0x14, 0x94, 0x54, 0xD4, 0x34, 0xB4, 0x74, 0xF4, 0x0C, 0x8C, 0x4C, 0xCC, 0x2C, 0xAC, 0x6C, 0xEC, 0x1C, 0x9C, 0x5C, 0xDC, 0x3C, 0xBC, 0x7C, 0xFC, 0x02, 0x82, 0x42, 0xC2, 0x22, 0xA2, 0x62, 0xE2, 0x12, 0x92, 0x52, 0xD2, 0x32, 0xB2, 0x72, 0xF2, 0x0A, 0x8A, 0x4A, 0xCA, 0x2A, 0xAA, 0x6A, 0xEA, 0x1A, 0x9A, 0x5A, 0xDA, 0x3A, 0xBA, 0x7A, 0xFA, 0x06, 0x86, 0x46, 0xC6, 0x26, 0xA6, 0x66, 0xE6, 0x16, 0x96, 0x56, 0xD6, 0x36, 0xB6, 0x76, 0xF6, 0x0E, 0x8E, 0x4E, 0xCE, 0x2E, 0xAE, 0x6E, 0xEE, 0x1E, 0x9E, 0x5E, 0xDE, 0x3E, 0xBE, 0x7E, 0xFE, 0x01, 0x81, 0x41, 0xC1, 0x21, 0xA1, 0x61, 0xE1, 0x11, 0x91, 0x51, 0xD1, 0x31, 0xB1, 0x71, 0xF1, 0x09, 0x89, 0x49, 0xC9, 0x29, 0xA9, 0x69, 0xE9, 0x19, 0x99, 0x59, 0xD9, 0x39, 0xB9, 0x79, 0xF9, 0x05, 0x85, 0x45, 0xC5, 0x25, 0xA5, 0x65, 0xE5, 0x15, 0x95, 0x55, 0xD5, 0x35, 0xB5, 0x75, 0xF5, 0x0D, 0x8D, 0x4D, 0xCD, 0x2D, 0xAD, 0x6D, 0xED, 0x1D, 0x9D, 0x5D, 0xDD, 0x3D, 0xBD, 0x7D, 0xFD, 0x03, 0x83, 0x43, 0xC3, 0x23, 0xA3, 0x63, 0xE3, 0x13, 0x93, 0x53, 0xD3, 0x33, 0xB3, 0x73, 0xF3, 0x0B, 0x8B, 0x4B, 0xCB, 0x2B, 0xAB, 0x6B, 0xEB, 0x1B, 0x9B, 0x5B, 0xDB, 0x3B, 0xBB, 0x7B, 0xFB, 0x07, 0x87, 0x47, 0xC7, 0x27, 0xA7, 0x67, 0xE7, 0x17, 0x97, 0x57, 0xD7, 0x37, 0xB7, 0x77, 0xF7, 0x0F, 0x8F, 0x4F, 0xCF, 0x2F, 0xAF, 0x6F, 0xEF, 0x1F, 0x9F, 0x5F, 0xDF, 0x3F, 0xBF, 0x7F, 0xFF]

class LiveTeletextConverter:
    def __init__(self, stream_url, teletext_pid):
        self.stream_url = stream_url
        self.teletext_pid = teletext_pid
        
        # State from pes2t42.py
        self.line_offset = 0
        self.field_parity = 1
        self.fieldbytes = bytearray(42 * 16)
        
    def process_pes_data(self, pes_data):
        """Process PES payload data - direct from pes2t42.py logic"""
        outputs = []
        
        # Read 9-byte PES header
        if len(pes_data) < 9:
            return outputs
            
        prefix = int.from_bytes(pes_data[0:3], "big")
        if prefix != 1:
            print("Missing PES header. Skipping", file=sys.stderr)
            return outputs
        
        if pes_data[3] != 0xBD:
            print("Invalid stream ID", file=sys.stderr)
            return outputs
        
        length = int.from_bytes(pes_data[4:6], "big")
        headerlength = pes_data[8]
        
        # Extract packet data
        data_start = 9 + headerlength
        data_end = 6 + length if length > 0 else len(pes_data)
        
        if data_end > len(pes_data):
            return outputs
        
        packet = pes_data[data_start:data_end]
        
        if len(packet) < 1:
            return outputs
        
        # Check data identifier for EBU data
        if packet[0] < 0x10 or packet[0] > 0x1F:
            return outputs
        
        # Process data units - EXACT copy from pes2t42.py
        for i in range(1, len(packet), 0x2E):
            if i + 0x2E > len(packet):
                break
                
            if packet[i] == 0x02 or packet[i] == 0x03:  # id is EBU teletext
                datafield = packet[i+2:i+0x2E]  # ignore unit length
                
                if len(datafield) < 0x2C:
                    continue
                
                fp = (datafield[0] >> 5) & 1
                lo = datafield[0] & 0x1F
                
                if lo < 0x07 or lo > 0x16:
                    print(f"Invalid line offset {lo}", file=sys.stderr)
                    continue
                
                # Field parity changed - output previous field
                if fp != self.field_parity:
                    outputs.append(bytes(self.fieldbytes))
                    self.field_parity = fp
                    self.fieldbytes = bytearray(42 * 16)  # clear lines
                    self.line_offset = 0
                
                # Check line offset ordering
                if lo < self.line_offset:
                    print(f"Line offset decreased from {self.line_offset} to {lo}", file=sys.stderr)
                    # Continue anyway for live stream
                
                # Copy line data with bit reversal
                for j in range(0x2A):
                    self.fieldbytes[(lo - 7) * 0x2A + j] = REVERSE_BYTES[datafield[2 + j]]
                
                self.line_offset = lo
        
        return outputs
    
    def run(self):
        """Main streaming loop"""
        print(f"Connecting to {self.stream_url}", file=sys.stderr)
        print(f"Filtering teletext PID: 0x{self.teletext_pid:04x}", file=sys.stderr)
        print(f"Output: T42 stream to stdout", file=sys.stderr)
        
        try:
            output = sys.stdout.buffer
            
            with requests.get(self.stream_url, stream=True, timeout=10) as response:
                response.raise_for_status()
                
                field_count = 0
                pes_buffer = bytearray()
                in_pes = False
                
                for chunk in response.iter_content(chunk_size=188 * 100):
                    # Process TS packets - logic from ts2pes.py
                    for i in range(0, len(chunk), 188):
                        if i + 188 > len(chunk):
                            break
                        
                        packet = chunk[i:i+188]
                        
                        if len(packet) != 188:
                            continue
                        
                        if packet[0] != 0x47:
                            print("Packet without sync byte", file=sys.stderr)
                            continue
                        
                        PID = ((packet[1] & 0x1F) << 8) | packet[2]
                        
                        if PID != self.teletext_pid:
                            continue
                        
                        PUSI = (packet[1] >> 6) & 1
                        Adaption = (packet[3] >> 4) & 3
                        
                        # Extract payload - exact from ts2pes.py
                        payload = None
                        if Adaption == 1:
                            payload = packet[4:188]
                        elif Adaption == 3:
                            payload = packet[5 + packet[4]:188]
                        
                        if payload is None:
                            continue
                        
                        # Handle PES packet boundaries
                        if PUSI:
                            # Process complete PES packet
                            if len(pes_buffer) > 0:
                                fields = self.process_pes_data(bytes(pes_buffer))
                                for field in fields:
                                    output.write(field)
                                    output.flush()
                                    field_count += 1
                                    if field_count % 50 == 0:
                                        print(f"Fields: {field_count}", file=sys.stderr)
                            
                            # Start new PES packet
                            pes_buffer = bytearray(payload)
                            in_pes = True
                        elif in_pes:
                            # Continue building PES packet
                            pes_buffer.extend(payload)
                
        except KeyboardInterrupt:
            print("\nStopped by user", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: teletext_live_fixed.py <stream_url> <pid_hex>", file=sys.stderr)
        print("Example: teletext_live_fixed.py http://192.168.1.9:9981/stream/... 0835 | vbit-iv.py 1 0", file=sys.stderr)
        sys.exit(1)
    
    stream_url = sys.argv[1]
    pid_hex = sys.argv[2]
    
    try:
        teletext_pid = int(pid_hex, 16)
    except ValueError:
        print(f"Error: Invalid PID '{pid_hex}'. Must be hexadecimal.", file=sys.stderr)
        sys.exit(1)
    
    converter = LiveTeletextConverter(stream_url, teletext_pid)
    converter.run()

if __name__ == "__main__":
    main()
