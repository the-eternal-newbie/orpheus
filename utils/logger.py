import re
import shutil
import sys
import time
import threading

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

# For cross-platform color support
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Auto-reset colors after each print
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    print("Warning: Install 'colorama' for colored output: pip install colorama")
    
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = BLACK = ''
        LIGHTRED_EX = LIGHTGREEN_EX = LIGHTYELLOW_EX = LIGHTBLUE_EX = ''
        LIGHTMAGENTA_EX = LIGHTCYAN_EX = LIGHTWHITE_EX = LIGHTBLACK_EX = ''
        RESET = ''
    
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = BLACK = ''
        RESET = ''
    
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''


class LogLevel(Enum):
    DEBUG = ("DEBUG", Fore.CYAN, "🔍")
    INFO = ("INFO", Fore.BLUE, "ℹ️")
    SUCCESS = ("SUCCESS", Fore.GREEN, "✅")
    WARNING = ("WARNING", Fore.YELLOW, "⚠️")
    ERROR = ("ERROR", Fore.RED, "❌")
    CRITICAL = ("CRITICAL", Fore.RED + Style.BRIGHT, "🚨")


class SpinnerStyle(Enum):
    DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    DOTS2 = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    DOTS3 = ["⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓"]
    CIRCLE = ["◐", "◓", "◑", "◒"]
    BRAILLE = ["⡀", "⡄", "⡆", "⡇", "⡏", "⡟", "⡿", "⣿", "⣷", "⣶", "⣴", "⣤", "⣀"]
    MUSIC = ["♪", "♫", "♬", "♭", "♮", "♯"]
    ARROW = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
    BOUNCING = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]

class SectionColors(Enum):
    A = Fore.RED
    B = Fore.GREEN
    C = Fore.YELLOW
    D = Fore.BLUE
    E = Fore.MAGENTA
    F = Fore.CYAN
    G = Fore.WHITE
    H = Fore.LIGHTBLACK_EX
    I = Fore.LIGHTWHITE_EX
    J = Fore.LIGHTRED_EX
    K = Fore.LIGHTGREEN_EX
    L = Fore.LIGHTYELLOW_EX
    M = Fore.LIGHTBLUE_EX
    N = Fore.LIGHTMAGENTA_EX
    O = Fore.LIGHTCYAN_EX
    P = Fore.LIGHTWHITE_EX

class RadLogger:
    ASCII_ART = {
        'generic': './ascii/logo.txt',
    }
    
    root = './logs/'
    
    def __init__(self, 
                 name: str = "RadLogger",
                 show_timestamp: bool = True,
                 show_emoji: bool = True,
                 colored: bool = True,
                 log_file: Optional[str] = None):
        """
        Initialize the Music Logger
        
        Args:
            name: Logger name/identifier
            show_timestamp: Whether to show timestamps
            show_emoji: Whether to show emojis (set False for terminals that don't support them)
            colored: Whether to use colors
            log_file: Optional file path to save logs
        """
        self.name = name
        self.show_timestamp = show_timestamp
        self.show_emoji = show_emoji
        self.colored = colored and COLORS_AVAILABLE
        self.log_file = log_file
        self.indent_level = 0
        self._spinner_active = False
        self._spinner_thread = None
        self._progress_active = False
        
        # Terminal width for formatting
        self.terminal_width = shutil.get_terminal_size((80, 20)).columns
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': None,
            'operations': []
        }
        
        if self.log_file:
            with open(self.root + self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Session started: {datetime.now()}\n")
                f.write(f"{'='*50}\n")

    def __hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def __show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    
    def __get_timestamp(self) -> str:
        if self.show_timestamp:
            return f"[{datetime.now().strftime('%H:%M:%S')}]"
        return ""
    
    def __get_emoji(self, level: LogLevel) -> str:
        if self.show_emoji:
            return level.value[2]
        return ""
    
    def __get_color(self, level: LogLevel) -> str:
        if self.colored:
            return level.value[1]
        return ""
    
    def __read_ascii_file(self, path: Path) -> list[str]:
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            print(f"{Fore.RED}Error reading file: {e}{Style.RESET_ALL}", file=sys.stderr)
            sys.exit(1)
    
    def __write_to_file(self, message: str):
        if self.log_file:
            with open(self.root + self.log_file, 'a', encoding='utf-8') as f:
                # Strip color codes for file output
                clean_message = self.__strip_colors(message)
                f.write(f"{clean_message}\n")
    
    def __strip_colors(self, text: str) -> str:
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def __format_message(self, message: str, level: LogLevel) -> str:
        indent = "  " * self.indent_level
        timestamp = self.__get_timestamp()
        emoji = self.__get_emoji(level)
        color = self.__get_color(level)
        reset = Style.RESET_ALL if self.colored else ""
        
        parts = []
        if timestamp:
            parts.append(f"{Fore.LIGHTBLACK_EX if self.colored else ''}{timestamp}{reset}")
        if emoji:
            parts.append(emoji)
        
        prefix = " ".join(parts)
        if prefix:
            prefix += " "
        
        return f"{indent}{prefix}{color}{message}{reset}"

    def clear_screen(self):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        formatted = self.__format_message(message, level)
        print(formatted)
        self.__write_to_file(formatted)
        
        # Update statistics
        if level == LogLevel.ERROR:
            self.stats['errors'] += 1
        elif level == LogLevel.WARNING:
            self.stats['warnings'] += 1
    
    def debug(self, message: str):
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        self.log(message, LogLevel.INFO)
    
    def success(self, message: str):
        self.log(message, LogLevel.SUCCESS)
    
    def warning(self, message: str):
        self.log(message, LogLevel.WARNING)
    
    def error(self, message: str):
        self.log(message, LogLevel.ERROR)
    
    def critical(self, message: str):
        self.log(message, LogLevel.CRITICAL)
    
    def header(self, text: str, style: str = "double"):
        """Print a styled header"""
        styles = {
            "single": ("─", "┌", "┐", "└", "┘", "│"),
            "double": ("═", "╔", "╗", "╚", "╝", "║"),
            "thick": ("━", "┏", "┓", "┗", "┛", "┃"),
            "ascii": ("-", "+", "+", "+", "+", "|")
        }
        
        chars = styles.get(style, styles["double"])
        line, tl, tr, bl, br, vert = chars
        
        # Center the text
        padding = 4
        text_with_padding = f" {text} "
        width = max(len(text_with_padding) + padding * 2, 40)
        centered = text_with_padding.center(width)
        
        color = Fore.CYAN if self.colored else ""
        reset = Style.RESET_ALL if self.colored else ""
        
        print(f"{color}{tl}{line * width}{tr}")
        print(f"{vert}{centered}{vert}")
        print(f"{bl}{line * width}{br}{reset}")
        self.__write_to_file(f"\n{text}\n" + "=" * width)
    
    def ascii_art(self, service: str = "generic"):
        self.__hide_cursor()
        print('\n\n')
        art = self.ASCII_ART.get(service.lower(), self.ASCII_ART["generic"])
        lines = self.__read_ascii_file(Path(art))
        
        default_color = Fore.MAGENTA if self.colored else ""

        token_re = re.compile(r"\{(\w+)\}")

        def write_segment(seg: str, color_code: str):
            for ch in seg:
                sys.stdout.write((color_code if self.colored else "") + ch + Style.RESET_ALL)
                sys.stdout.flush()
                if ch != " ":
                    time.sleep(0.001)
        
        current_color = default_color
        
        try:
            for line in lines:
                pos = 0
                for m in token_re.finditer(line):
                    write_segment(line[pos:m.start()], current_color)
                    token_id = m.group(1)
                    current_color = SectionColors[token_id].value if self.colored else ""
                    pos = m.end()

                write_segment(line[pos:], current_color)
                sys.stdout.write("\n")
                sys.stdout.flush()
        finally:
            print('\n\n')
            self.__write_to_file(art)
            self.__show_cursor()
        
    
    def progress_bar(self, current: int, total: int, 
                    prefix: str = "", suffix: str = "",
                    length: int = 40, fill: str = "█"):
        percent = current / total if total > 0 else 0
        filled_length = int(length * percent)
        
        # Color gradient for progress
        if self.colored:
            if percent < 0.33:
                color = Fore.RED
            elif percent < 0.66:
                color = Fore.YELLOW
            else:
                color = Fore.GREEN
        else:
            color = ""
        
        reset = Style.RESET_ALL if self.colored else ""
        
        bar = f"{fill * filled_length}{'-' * (length - filled_length)}"
        
        line = f"\r{prefix} |{color}{bar}{reset}| {percent*100:.1f}% {suffix}"
        
        # Print without newline
        sys.stdout.write(line)
        sys.stdout.flush()
        
        # Add newline when complete
        if current >= total:
            print()
            self.__write_to_file(f"{prefix} - Completed 100%")
    
    def spinner(self, message: str, style: SpinnerStyle = SpinnerStyle.DOTS):
        self._spinner_active = True
        
        def spin():
            frames = style.value
            idx = 0
            while self._spinner_active:
                frame = frames[idx % len(frames)]
                sys.stdout.write(f"\r{frame} {message}")
                sys.stdout.flush()
                idx += 1
                time.sleep(0.1)
            sys.stdout.write("\r" + " " * (len(message) + 3) + "\r")
            sys.stdout.flush()
        
        self._spinner_thread = threading.Thread(target=spin)
        self._spinner_thread.daemon = True
        self._spinner_thread.start()
    
    def stop_spinner(self, final_message: Optional[str] = None, success: bool = True):
        self._spinner_active = False
        if self._spinner_thread:
            self._spinner_thread.join(timeout=0.5)
        
        if final_message:
            if success:
                self.success(final_message)
            else:
                self.error(final_message)
    
    def section(self, title: str):
        color = Fore.LIGHTYELLOW_EX if self.colored else ""
        reset = Style.RESET_ALL if self.colored else ""
        print(f"\n{color}▶ {title}{reset}")
        self.__write_to_file(f"\n▶ {title}")
        self.indent_level += 1
    
    def end_section(self):
        self.indent_level = max(0, self.indent_level - 1)
    
    def table(self, data: List[List[str]], headers: Optional[List[str]] = None):
        if not data:
            return
        
        # Calculate column widths
        all_rows = [headers] + data if headers else data
        col_widths = []
        for col in range(len(all_rows[0])):
            max_width = max(len(str(row[col])) for row in all_rows if col < len(row))
            col_widths.append(max_width)
        
        # Print table
        color = Fore.CYAN if self.colored else ""
        reset = Style.RESET_ALL if self.colored else ""
        
        # Header
        if headers:
            header_row = " │ ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
            print(f"{color}│ {header_row} │")
            separator = "─┼─".join("─" * w for w in col_widths)
            print(f"├─{separator}─┤{reset}")
        
        # Data rows
        for row in data:
            row_str = " │ ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            print(f"│ {row_str} │")
    
    def tree(self, items: Dict[str, Any], prefix: str = ""):
        items_list = list(items.items())
        for i, (key, value) in enumerate(items_list):
            is_last = i == len(items_list) - 1
            
            # Choose the right symbol
            symbol = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            
            color = Fore.GREEN if self.colored else ""
            reset = Style.RESET_ALL if self.colored else ""
            
            print(f"{prefix}{color}{symbol}{key}{reset}")
            
            # Recursively print nested dictionaries
            if isinstance(value, dict):
                self.tree(value, prefix + extension)
            elif isinstance(value, list):
                for item in value:
                    print(f"{prefix}{extension}• {item}")
    
    def file_operation(self, operation: str, filename: str, 
                      size: Optional[int] = None, success: bool = True):
        icons = {
            "read": "📖",
            "write": "💾",
            "delete": "🗑️",
            "copy": "📋",
            "move": "📦",
            "download": "⬇️",
            "upload": "⬆️",
            "process": "⚙️"
        }
        
        icon = icons.get(operation.lower(), "📄") if self.show_emoji else ""
        
        size_str = ""
        if size:
            size_str = self._format_bytes(size)
            size_str = f" ({size_str})"
        
        status = "✓" if success else "✗"
        color = Fore.GREEN if success else Fore.RED
        
        message = f"{icon} {operation.capitalize()}: {filename}{size_str} {status}"
        
        if success:
            self.success(message)
            self.stats['files_processed'] += 1
        else:
            self.error(message)
    
    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def statistics(self):
        self.header("Session Statistics", style="single")
        
        stats_data = [
            ["Files Processed", str(self.stats['files_processed'])],
            ["Errors", str(self.stats['errors'])],
            ["Warnings", str(self.stats['warnings'])]
        ]
        
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            stats_data.append(["Duration", str(duration).split('.')[0]])
        
        self.table(stats_data, headers=["Metric", "Value"])
    
    def divider(self, char: str = "─", length: Optional[int] = None):
        if length is None:
            length = min(self.terminal_width, 60)
        
        color = Fore.LIGHTBLACK_EX if self.colored else ""
        reset = Style.RESET_ALL if self.colored else ""
        
        print(f"{color}{char * length}{reset}")
        self.__write_to_file(char * length)
    
    def track_operation(self, operation_name: str):
        return OperationTracker(self, operation_name)
    
    def batch_progress(self, items: list, operation: Callable, 
                      description: str = "Processing"):
        total = len(items)
        
        for i, item in enumerate(items, 1):
            self.progress_bar(i, total, 
                            prefix=f"{description}",
                            suffix=f"({i}/{total})")
            
            try:
                operation(item)
            except Exception as e:
                self.error(f"Failed processing item {i}: {e}")
        
        self.success(f"{description} completed: {total} items")


class OperationTracker:
    """Context manager for tracking operation time"""
    
    def __init__(self, logger: RadLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation_name}")
        self.logger.indent_level += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.indent_level = max(0, self.logger.indent_level - 1)
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.success(
                f"Completed: {self.operation_name} "
                f"(took {elapsed:.2f}s)"
            )
        else:
            self.logger.error(
                f"Failed: {self.operation_name} "
                f"(after {elapsed:.2f}s): {exc_val}"
            )
        
        # Record in statistics
        self.logger.stats['operations'].append({
            'name': self.operation_name,
            'duration': elapsed,
            'success': exc_type is None
        })