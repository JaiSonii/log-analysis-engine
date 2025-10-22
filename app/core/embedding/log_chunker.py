from datetime import datetime
import re
from .types import Log, Chunk, ChunkMetaData

class LogChunker:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _create_sliding_window(file_path: str, window_size: int):
        """Generator that yields sliding windows of lines from the file."""
        lines = []
        with open(file_path, 'r') as f:
            for _ in range(window_size):
                line = f.readline()
                if not line: 
                    break
                lines.append(line)
            
            if lines: 
                yield lines[:]
            
            for line in f:
                lines.pop(0) 
                lines.append(line)
                yield lines[:]

    def _parse_log_line(self, line: str) -> Log:
        """
        Parse a log line to extract timestamp and check for errors. 
        Args:
            line : the log line
        Returns:
            An Object of Log
        """
        result = Log(timestamp=None, is_error=False, message=line, level=None)

        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?",
            r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}",              
            r"\w{3} \d{2} \d{2}:\d{2}:\d{2}"                     
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(0)
                    if "." in timestamp_str:  # Has milliseconds
                        result["timestamp"] = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    elif "/" in timestamp_str:  # Has forward slashes
                        result["timestamp"] = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                    elif len(timestamp_str) < 19:  # Short format
                        result["timestamp"] = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
                    else:  # Standard format
                        result["timestamp"] = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    break
                except ValueError:
                    continue
        
        error_patterns = [
            r"error",
            r"exception",
            r"fail",
            r"critical",
            r"fatal"
        ]
        
        line_lower = line.lower()
        result["is_error"] = any(pattern in line_lower for pattern in error_patterns)
        
        level_match = re.search(r"\[(ERROR|INFO|WARNING|DEBUG|CRITICAL)\]", line, re.IGNORECASE)
        if level_match:
            result["level"] = level_match.group(1).upper()
        
        return result

    def invoke(self, file_path: str, window_size: int = 100):
        """
        Creates a chunk iterator of window size over the the given log file
        Args:
            file_path : Path of the file
            window_size : number of log lines to include in a chunk (default: 100)
        Returns:
            Chunk : Generator Object of Chunks 
        """
        if not file_path:
            raise ValueError("file_path is required")
        
        for window in self._create_sliding_window(file_path, window_size):
            chunk = Chunk(text="", metadata=ChunkMetaData(start_timestamp=None, end_timestamp=None, has_error=False))

            parsed_firstline = self._parse_log_line(window[0].strip())
            parsed_lastline = self._parse_log_line(window[-1].strip())

            chunk['metadata']['start_timestamp'] = parsed_firstline['timestamp']
            chunk['metadata']['end_timestamp'] = parsed_lastline['timestamp']

            for line in window:
                parsed_line = self._parse_log_line(line.strip())
                chunk['text'] += f"{parsed_line['message']}\n"
                chunk['metadata']['has_error'] = chunk['metadata']["has_error"] | parsed_line['is_error'] 
                
            yield chunk



if __name__ == "__main__":
    chunker = LogChunker()
    log_path = "C:\\Machine Learning\\log-analyzer\\data\\python.log"
    for chunk in chunker.invoke(log_path):
        print(chunk)
        break