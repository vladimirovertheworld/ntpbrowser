import ntplib
import concurrent.futures
import time
import curses
from datetime import datetime, timezone

# List of NTP servers
NTP_SERVERS = [
    "pool.ntp.org", "time.google.com", "time.cloudflare.com", "time.apple.com",
    "time.windows.com", "time.nist.gov", "ntp.ubuntu.com", "amazon.pool.ntp.org",
    "time.facebook.com", "ntp1.hetzner.de", "ntp.ripe.net", "ptbtime1.ptb.de",
    "ntp.se", "time.fu-berlin.de", "ntp.tuxfamily.net"
]

# Color schemes
COLOR_SCHEMES = [
    {
        'name': 'Light',
        'bg': curses.COLOR_WHITE,
        'fg': curses.COLOR_BLACK,
        'header': curses.COLOR_BLUE,
        'highlight': curses.COLOR_CYAN,
    },
    {
        'name': 'Solarized Light',
        'bg': curses.COLOR_YELLOW,
        'fg': curses.COLOR_BLACK,
        'header': curses.COLOR_BLUE,
        'highlight': curses.COLOR_CYAN,
    },
    {
        'name': 'Solarized Dark',
        'bg': curses.COLOR_BLACK,
        'fg': curses.COLOR_GREEN,
        'header': curses.COLOR_BLUE,
        'highlight': curses.COLOR_CYAN,
    },
    {
        'name': 'Dark',
        'bg': curses.COLOR_BLACK,
        'fg': curses.COLOR_WHITE,
        'header': curses.COLOR_YELLOW,
        'highlight': curses.COLOR_MAGENTA,
    },
    {
        'name': 'Blue',
        'bg': curses.COLOR_BLUE,
        'fg': curses.COLOR_WHITE,
        'header': curses.COLOR_YELLOW,
        'highlight': curses.COLOR_CYAN,
    }
]

# Man page content
MAN_PAGE = """
NTP Server Monitor - Help Page

DESCRIPTION
    This application monitors multiple NTP servers and displays their status and performance metrics.

DISPLAY COLUMNS
    Server:         The hostname of the NTP server
    RTT (ms):       Round Trip Time in milliseconds. Format: current (min-max)
    Offset (s):     Time offset from the server in seconds. Format: current (min-max)
    NTP Time:       Current time reported by the NTP server
    Root Delay:     Total network path delay to the reference clock. Format: current (min-max)
    Root Disp:      Total dispersion to the reference clock. Format: current (min-max)
    Stratum:        The stratum level of the server. Format: current (min-max)

METRICS EXPLANATION
    RTT (Round Trip Time):
        The time it takes for a request to go to the server and come back.
        Lower values indicate better network connectivity.

    Offset:
        The time difference between your system and the NTP server.
        Closer to zero indicates better synchronization.

    Root Delay:
        The total delay along the path to the stratum 1 time source.
        Lower values are generally better.

    Root Dispersion:
        The maximum error relative to the primary reference source.
        Lower values indicate higher accuracy.

    Stratum:
        Indicates how many hops away the server is from a primary time source.
        Lower numbers (especially 1 or 2) are typically more reliable.

COLOR CODING
    The table alternates between two colors for better readability.
    The header and footer use a distinct color for emphasis.

COMMANDS
    q: Quit the application
    c: Cycle through available color schemes
    h: Display this help page
    Up/Down Arrow Keys: Select a server
    d: Display detailed information for the selected server

UPDATE FREQUENCY
    The application queries NTP servers every 5 seconds and updates the display.

Press any key to return to the main display.
"""

class ServerStats:
    def __init__(self):
        self.rtt_min = float('inf')
        self.rtt_max = float('-inf')
        self.offset_min = float('inf')
        self.offset_max = float('-inf')
        self.delay_min = float('inf')
        self.delay_max = float('-inf')
        self.dispersion_min = float('inf')
        self.dispersion_max = float('-inf')
        self.stratum_min = float('inf')
        self.stratum_max = float('-inf')

    def update(self, rtt, offset, delay, dispersion, stratum):
        self.rtt_min = min(self.rtt_min, rtt)
        self.rtt_max = max(self.rtt_max, rtt)
        self.offset_min = min(self.offset_min, offset)
        self.offset_max = max(self.offset_max, offset)
        self.delay_min = min(self.delay_min, delay)
        self.delay_max = max(self.delay_max, delay)
        self.dispersion_min = min(self.dispersion_min, dispersion)
        self.dispersion_max = max(self.dispersion_max, dispersion)
        self.stratum_min = min(self.stratum_min, stratum)
        self.stratum_max = max(self.stratum_max, stratum)

server_stats = {server: ServerStats() for server in NTP_SERVERS}

def query_ntp_server(server):
    client = ntplib.NTPClient()
    try:
        start = time.time()
        response = client.request(server, timeout=2)
        end = time.time()
        rtt = (end - start) * 1000  # Convert to milliseconds
        ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
        server_stats[server].update(rtt, response.offset, response.root_delay, response.root_dispersion, response.stratum)
        return (server, rtt, response.offset, ntp_time, response.root_delay, response.root_dispersion, response.stratum, response)
    except Exception as e:
        return (server, float('inf'), None, None, None, None, None, None)

def get_ntp_data():
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(query_ntp_server, NTP_SERVERS))
    return sorted(results, key=lambda x: x[1])

def draw_table(stdscr, data, color_scheme, selected_row):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    curses.init_pair(1, color_scheme['fg'], color_scheme['bg'])
    curses.init_pair(2, color_scheme['header'], color_scheme['bg'])
    curses.init_pair(3, color_scheme['fg'], color_scheme['highlight'])
    curses.init_pair(4, color_scheme['bg'], color_scheme['fg'])  # Inverted colors for selection
    
    header = f"{'Server':<20} {'RTT (ms)':<20} {'Offset (s)':<20} {'NTP Time':<21} {'Root Delay':<20} {'Root Disp':<20} {'Stratum':<7}"
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(0, 0, header[:width-1])
    stdscr.attroff(curses.color_pair(2))
    
    for i, (server, rtt, offset, ntp_time, root_delay, root_dispersion, stratum, _) in enumerate(data[:height-3], 1):
        if i - 1 == selected_row:
            stdscr.attron(curses.color_pair(4))
        elif i % 2 == 0:
            stdscr.attron(curses.color_pair(3))
        else:
            stdscr.attron(curses.color_pair(1))
        
        stats = server_stats[server]
        if rtt != float('inf'):
            row = (
                f"{server:<20} "
                f"{rtt:<7.2f}({stats.rtt_min:.2f}-{stats.rtt_max:.2f}) "
                f"{offset:<7.6f}({stats.offset_min:.6f}-{stats.offset_max:.6f}) "
                f"{ntp_time.strftime('%Y-%m-%d %H:%M:%S'):<21} "
                f"{root_delay:<7.6f}({stats.delay_min:.6f}-{stats.delay_max:.6f}) "
                f"{root_dispersion:<7.6f}({stats.dispersion_min:.6f}-{stats.dispersion_max:.6f}) "
                f"{stratum:<2}({stats.stratum_min}-{stats.stratum_max})"
            )
        else:
            row = f"{server:<20} {'Timeout':<20} {'N/A':<20} {'N/A':<21} {'N/A':<20} {'N/A':<20} {'N/A':<7}"
        stdscr.addstr(i, 0, row[:width-1])
        
        if i - 1 == selected_row:
            stdscr.attroff(curses.color_pair(4))
        elif i % 2 == 0:
            stdscr.attroff(curses.color_pair(3))
        else:
            stdscr.attroff(curses.color_pair(1))
    
    footer = f"Press 'q' to quit, 'c' to change color scheme, 'h' for help, 'd' for details (Current: {color_scheme['name']})"
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(height-1, 0, footer[:width-1])
    stdscr.attroff(curses.color_pair(2))
    
    stdscr.refresh()

def display_help(stdscr, color_scheme):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    curses.init_pair(1, color_scheme['fg'], color_scheme['bg'])
    curses.init_pair(2, color_scheme['header'], color_scheme['bg'])
    
    lines = MAN_PAGE.split('\n')
    
    for i, line in enumerate(lines):
        if i < height - 1:
            if i == 0:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(i, 0, line[:width-1])
                stdscr.attroff(curses.color_pair(2))
            else:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i, 0, line[:width-1])
                stdscr.attroff(curses.color_pair(1))
    
    stdscr.refresh()
    stdscr.getch()  # Wait for any key press

def display_detailed_info(stdscr, server_data, color_scheme):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    curses.init_pair(1, color_scheme['fg'], color_scheme['bg'])
    curses.init_pair(2, color_scheme['header'], color_scheme['bg'])
    
    server, rtt, offset, ntp_time, root_delay, root_dispersion, stratum, response = server_data
    
    if response is None:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, f"Detailed Information for {server}")
        stdscr.attroff(curses.color_pair(2))
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(2, 0, "Error: Unable to connect to the server")
        stdscr.attroff(curses.color_pair(1))
    else:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, f"Detailed Information for {server}")
        stdscr.attroff(curses.color_pair(2))
        
        stdscr.attron(curses.color_pair(1))
        
        # Handle ref_id which can be bytes or int
        if isinstance(response.ref_id, bytes):
            ref_id = response.ref_id.decode('ascii', errors='replace')
        elif isinstance(response.ref_id, int):
            ref_id = f"{response.ref_id:08x}"  # Convert int to hex string
        else:
            ref_id = str(response.ref_id)
        
        info = [
            f"NTP version: {response.version}",
            f"Leap indicator: {response.leap}",
            f"Mode: {response.mode}",
            f"Stratum: {stratum}",
            f"Precision: {response.precision}",
            f"Root delay: {root_delay:.6f} seconds",
            f"Root dispersion: {root_dispersion:.6f} seconds",
            f"Reference ID: {ref_id}",
            f"Reference timestamp: {datetime.fromtimestamp(response.ref_timestamp, timezone.utc)}",
            f"Originate timestamp: {datetime.fromtimestamp(response.orig_timestamp, timezone.utc)}",
            f"Receive timestamp: {datetime.fromtimestamp(response.recv_timestamp, timezone.utc)}",
            f"Transmit timestamp: {datetime.fromtimestamp(response.tx_timestamp, timezone.utc)}",
            f"Destination timestamp: {datetime.fromtimestamp(response.dest_timestamp, timezone.utc)}",
            f"Round trip time: {rtt:.2f} ms",
            f"Offset: {offset:.6f} seconds",
            f"Delay: {response.delay:.6f} seconds",
            f"Poll: {response.poll} seconds"
        ]
        
        for i, line in enumerate(info, 2):
            if i < height - 1:
                stdscr.addstr(i, 0, line[:width-1])
        
        stdscr.addstr(height-1, 0, "Press 'q' to return to the server list")
        stdscr.attroff(curses.color_pair(1))
    
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
            
def main(stdscr):
    curses.curs_set(0)  # Hide cursor
    stdscr.timeout(100)  # Set getch() timeout to 100ms for responsive input
    current_scheme = 0
    selected_row = 0
    
    # Set up colors
    curses.start_color()
    curses.use_default_colors()
    
    last_update = 0
    data = []
    while True:
        current_time = time.time()
        if current_time - last_update >= 5 or not data:  # Update every 5 seconds or if data is empty
            data = get_ntp_data()
            last_update = current_time
        
        draw_table(stdscr, data, COLOR_SCHEMES[current_scheme], selected_row)
        
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('c'):
            current_scheme = (current_scheme + 1) % len(COLOR_SCHEMES)
        elif key == ord('h'):
            display_help(stdscr, COLOR_SCHEMES[current_scheme])
        elif key == curses.KEY_UP and selected_row > 0:
            selected_row -= 1
        elif key == curses.KEY_DOWN and selected_row < len(data) - 1:
            selected_row += 1
        elif key == ord('d'):
            display_detailed_info(stdscr, data[selected_row], COLOR_SCHEMES[current_scheme])
        
        time.sleep(0.1)  # Small sleep to prevent high CPU usage

if __name__ == "__main__":
    curses.wrapper(main)