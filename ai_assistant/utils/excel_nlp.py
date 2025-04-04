import re
import logging
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from .excel_handler import ExcelHandler

logger = logging.getLogger("ai_assistant")

class ExcelNLProcessor:
    """Process natural language commands for Excel operations."""
    
    def __init__(self):
        """Initialize the Excel NL processor."""
        # Patterns for common operations
        self.patterns = {
            "show_file": re.compile(r"(?:show|open|display|view)\s+(?:the\s+)?(?:excel|spreadsheet|file)\s+(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", re.I),
            "list_files": re.compile(r"(?:list|show|find)\s+(?:all\s+)?(?:excel|spreadsheet)s?(?:\s+in\s+([^\n]+?))?(?:\s|$)", re.I),
            "extract_data": re.compile(r"(?:extract|get|find|show)\s+(?:data|information|rows|columns)\s+(?:from|in)\s+(?:the\s+)?(?:excel|spreadsheet|file)\s+(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", re.I),
            "analyze": re.compile(r"(?:analyze|summarize|describe)\s+(?:the\s+)?(?:excel|spreadsheet|file|data)\s+(?:(?:in|from)\s+)?(?:the\s+)?(?:excel|spreadsheet|file)?\s*(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", re.I),
            "create_chart": re.compile(r"(?:create|make|generate|plot)\s+(?:a\s+)?(\w+)(?:\s+chart|\s+graph|\s+plot)(?:\s+(?:from|in|of|using)\s+)?(?:the\s+)?(?:excel|spreadsheet|file|data)?\s*(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", re.I),
            "filter_data": re.compile(r"(?:filter|query|find|show)\s+(?:rows|data|information)(?:\s+(?:where|with)\s+)?(.+?)(?:\s+(?:from|in)\s+)?(?:the\s+)?(?:excel|spreadsheet|file)?\s*(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", re.I),
        }
        
    def parse_command(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into an Excel operation.
        
        Args:
            query: Natural language query.
            
        Returns:
            Dictionary with the parsed operation details.
        """
        try:
            # Check for list files pattern
            list_match = self.patterns["list_files"].search(query)
            if list_match:
                directory = list_match.group(1) if list_match.groups() and list_match.group(1) else ""
                return {
                    "operation": "list_files",
                    "directory": directory
                }
                
            # Check for show file pattern
            show_match = self.patterns["show_file"].search(query)
            if show_match:
                file_name = show_match.group(1)
                # Check for sheet specification
                sheet_match = re.search(r"(?:sheet|tab)\s+(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", query, re.I)
                sheet_name = sheet_match.group(1) if sheet_match else None
                
                return {
                    "operation": "show_file",
                    "file_name": file_name,
                    "sheet_name": sheet_name
                }
                
            # Check for extract data pattern
            extract_match = self.patterns["extract_data"].search(query)
            if extract_match:
                file_name = extract_match.group(1)
                
                # Look for column specification
                columns_match = re.search(r"(?:columns?|fields?)\s+(?:called\s+)?[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", query, re.I)
                columns = columns_match.group(1).split(",") if columns_match else None
                
                # Look for row limits
                row_limit_match = re.search(r"(?:top|first)\s+(\d+)(?:\s+rows?)?", query, re.I)
                row_limit = int(row_limit_match.group(1)) if row_limit_match else None
                
                return {
                    "operation": "extract_data",
                    "file_name": file_name,
                    "columns": columns,
                    "row_limit": row_limit
                }
                
            # Check for analyze pattern
            analyze_match = self.patterns["analyze"].search(query)
            if analyze_match:
                file_name = analyze_match.group(1)
                
                # Determine analysis type
                analysis_type = "summary"  # Default
                if "correlat" in query.lower():
                    analysis_type = "correlation"
                elif "descri" in query.lower():
                    analysis_type = "descriptive"
                    
                return {
                    "operation": "analyze",
                    "file_name": file_name,
                    "analysis_type": analysis_type
                }
                
            # Check for create chart pattern
            chart_match = self.patterns["create_chart"].search(query)
            if chart_match:
                chart_type = chart_match.group(1).lower()
                file_name = chart_match.group(2)
                
                # Look for column specifications (improved pattern to handle spaces and special characters)
                x_col_match = re.search(r"(?:x(?:-axis)?|horizontal)\s+(?:is|as|with|using)\s+(?:the\s+)?(?:column\s+)?[\"\']?([^\"\'\n,]+(?:\s+[^\"\'\n,]+)*)[\"\']?(?:\s|$)", query, re.I)
                y_col_match = re.search(r"(?:y(?:-axis)?|vertical)\s+(?:is|as|with|using)\s+(?:the\s+)?(?:column\s+)?[\"\']?([^\"\'\n,]+(?:\s+[^\"\'\n,]+)*)[\"\']?(?:\s|$)", query, re.I)
                
                x_column = x_col_match.group(1).strip() if x_col_match else None
                y_column = y_col_match.group(1).strip() if y_col_match else None
                
                # Look for title
                title_match = re.search(r"(?:title|named|called)\s+[\"\']?([^\"\'\n]+?)[\"\']?(?:\s|$)", query, re.I)
                title = title_match.group(1) if title_match else f"{chart_type.capitalize()} Chart"
                
                return {
                    "operation": "create_chart",
                    "file_name": file_name,
                    "chart_type": chart_type,
                    "x_column": x_column,
                    "y_column": y_column,
                    "title": title
                }
                
            # Check for filter data pattern
            filter_match = self.patterns["filter_data"].search(query)
            if filter_match:
                conditions = filter_match.group(1)
                file_name = filter_match.group(2)
                
                return {
                    "operation": "filter_data",
                    "file_name": file_name,
                    "conditions": conditions
                }
                
            # If no specific pattern matches, try general interpretation
            return self._interpret_general_query(query)
            
        except Exception as e:
            logger.error(f"Error parsing Excel command: {e}")
            return {
                "operation": "error",
                "message": f"Could not parse the Excel command: {str(e)}"
            }
    
    def _interpret_general_query(self, query: str) -> Dict[str, Any]:
        """
        Attempt to interpret a general Excel-related query.
        
        Args:
            query: Natural language query.
            
        Returns:
            Dictionary with interpreted operation.
        """
        query_lower = query.lower()
        
        # Check for Excel-related keywords
        if any(word in query_lower for word in ["excel", "spreadsheet", "workbook", "sheet", "cell"]):
            # Extract potential file names
            file_matches = re.findall(r"[\w\-\s]+\.xlsx?", query)
            file_name = file_matches[0] if file_matches else None
            
            if "create" in query_lower or "new" in query_lower:
                return {
                    "operation": "create_file",
                    "file_name": file_name
                }
            elif "open" in query_lower or "show" in query_lower or "display" in query_lower:
                return {
                    "operation": "show_file",
                    "file_name": file_name
                }
            elif "delete" in query_lower or "remove" in query_lower:
                return {
                    "operation": "delete_file",
                    "file_name": file_name
                }
            else:
                # Default to general Excel query
                return {
                    "operation": "excel_query",
                    "query": query,
                    "file_name": file_name
                }
        else:
            # Not an Excel-related query
            return {
                "operation": "unknown",
                "query": query
            }
            
    def translate_to_pandas_query(self, conditions: str) -> str:
        """
        Translate natural language conditions to pandas query syntax.
        
        Args:
            conditions: Natural language conditions.
            
        Returns:
            Pandas query string.
        """
        try:
            # Map common phrases to operators
            operator_map = {
                "greater than": ">",
                "less than": "<",
                "equal to": "==",
                "equals": "==",
                "equal": "==",
                "not equal to": "!=",
                "not equals": "!=",
                "at least": ">=",
                "greater than or equal to": ">=",
                "at most": "<=",
                "less than or equal to": "<="
            }
            
            # Replace phrases with operators
            query = conditions
            for phrase, operator in operator_map.items():
                query = query.replace(phrase, operator)
                
            # Replace "and" with "&" and "or" with "|"
            query = re.sub(r'\band\b', '&', query)
            query = re.sub(r'\bor\b', '|', query)
            
            # Ensure column names with spaces are properly quoted
            col_pattern = re.compile(r'([a-zA-Z0-9_\s]+)\s*([<>=!]+)')
            query = col_pattern.sub(r'`\1` \2', query)
            
            return query
            
        except Exception as e:
            logger.error(f"Error translating to pandas query: {e}")
            return conditions  # Return original if translation fails
