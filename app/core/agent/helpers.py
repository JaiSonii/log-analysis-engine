from typing_extensions import List
import re
import xml.etree.ElementTree as ET

def extract_logs_from_repomix(repomix_context: str, start_str : str = "logger") -> List[str]:
    """
    Parses an XML repomix context, extracts code blocks,
    and finds potential logging statements using regex.
    Args:
        repomix_context : repomix xml code context
        start_str : starting string of logging (eg. - logging, logger), default - logger
    """
    found_logs = []
    
    # Regex to find lines containing common log function calls.
    # This looks for the keyword (logger.info, print, etc.)
    # followed by an open parenthesis.
    # Build the pattern safely by escaping the provided start_str.
    escaped_start = re.escape(start_str) if start_str else r'\w+'
    pattern = r".*(?:{start}\.(?:info|warning|error|debug|critical)|console\.(?:log|warn|error|debug)|print)\s*\(.*".format(start=escaped_start)
    log_pattern = re.compile(pattern, re.IGNORECASE)
    
    try:
        root = ET.fromstring(repomix_context)
        
        # Find all <code> tags anywhere in the XML tree
        code_elements = root.findall('.//code')
        
        if not code_elements:
            print("Warning: No <code> tags found in repomix_context. Check XML structure.")
            return []

        for code_element in code_elements:
            if code_element.text:
                code_block = code_element.text
                lines = code_block.split('\n')
                for line in lines:
                    # Search for the pattern in the line
                    if log_pattern.search(line):
                        stripped_line = line.strip()
                        if stripped_line and not stripped_line.lstrip().startswith(('#', '//', '/*')):
                            found_logs.append(stripped_line)
                            
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}. Ensure repomix-output.xml is valid XML.")
        print("As a fallback, trying to parse the entire file as plain text...")
        try:
            lines = repomix_context.split('\n')
            for line in lines:
                if log_pattern.search(line):
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.lstrip().startswith(('#', '//', '/*')):
                        found_logs.append(stripped_line.replace('{','[').replace('}',']'))
        except Exception as fallback_e:
            print(f"Fallback plain text parsing failed: {fallback_e}")
            
    return found_logs

def create_log_flow(repomix_context : str, log_start : str | None = None):
    """
    Local function to extract log statements from the repomix_context
    using XML parsing and RegEx.
    """
    log_list = []
    print("Extracting logs using local function...")
    try:
        
        if not repomix_context:
            print("Error: repomix_context is empty. Cannot analyze logs.")
            return []
        
        # Call the new helper function to do the work (use configured start token or default)
        start_str = log_start or 'logger'
        log_list = extract_logs_from_repomix(repomix_context, start_str)
        
        return log_list

    except Exception as e:
        print(f"An error occurred during log extraction: {e}")
        return []