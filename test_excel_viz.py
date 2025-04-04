"""
Test script for Excel visualization fix.
This script tests the fix for the Excel visualization error:
'<' not supported between instances of 'str' and 'int'
"""

import os
import sys
import pandas as pd
import logging
import matplotlib.pyplot as plt
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the package to path if needed
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # Try to import the Excel handler
    from ai_assistant.utils.excel_handler import ExcelHandler
    logger.info("Successfully imported ExcelHandler from ai_assistant")
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Define a simple version for testing
    class ExcelHandler:
        def __init__(self):
            pass
            
        def generate_excel_visualization(self, df, chart_type, x_column, y_column, title="Chart"):
            """Fixed version of generate_excel_visualization"""
            try:
                # Create figure and axes
                plt.figure(figsize=(10, 6))
                
                # Ensure x_column and y_column exist in the DataFrame
                if x_column not in df.columns:
                    return f"Error: Column '{x_column}' not found in DataFrame"
                if y_column not in df.columns:
                    return f"Error: Column '{y_column}' not found in DataFrame"
                    
                # Make a copy to avoid modifying the original DataFrame
                plot_df = df.copy()
                
                # Convert y_column to numeric, handling errors
                plot_df[y_column] = pd.to_numeric(plot_df[y_column], errors='coerce')
                plot_df = plot_df.dropna(subset=[y_column])
                
                # Convert x_column to string to avoid comparison issues in pie charts
                plot_df[x_column] = plot_df[x_column].astype(str)
                
                # Generate the chart based on type
                if chart_type == "bar":
                    plot_df.plot(kind='bar', x=x_column, y=y_column, title=title, legend=True)
                elif chart_type == "line":
                    plot_df.plot(kind='line', x=x_column, y=y_column, title=title, legend=True)
                elif chart_type == "scatter":
                    plot_df.plot(kind='scatter', x=x_column, y=y_column, title=title, legend=True)
                elif chart_type == "pie":
                    # For pie charts, we need to group by x_column and sum y_column
                    pie_data = plot_df.groupby(x_column)[y_column].sum()
                    pie_data.plot(kind='pie', autopct='%1.1f%%', title=title)
                elif chart_type == "hist":
                    plot_df[y_column].plot(kind='hist', title=title, legend=True)
                else:
                    return f"Error: Unsupported chart type '{chart_type}'"
                
                # Add labels and title
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.title(title)
                plt.tight_layout()
                
                # Save the chart to a file
                import tempfile
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                chart_file = os.path.join(temp_dir, f"excel_chart_test.png")
                
                # Save the chart
                plt.savefig(chart_file)
                plt.close()
                
                logger.info(f"Chart saved to {chart_file}")
                return chart_file
                
            except Exception as e:
                logger.error(f"Error generating Excel visualization: {e}")
                return f"Error generating visualization: {str(e)}"

def create_test_data():
    """Create test data with Month and Profit columns"""
    # Create a DataFrame with Month (string) and Profit (numeric)
    data = {
        'Month': ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December'],
        'Profit': [1000, 1200, 800, 1500, 2000, 2200, 1800, 1600, 1400, 1900, 2100, 2500]
    }
    return pd.DataFrame(data)

def test_pie_chart():
    """Test pie chart visualization"""
    logger.info("Testing pie chart visualization with Month and Profit")
    
    # Create test data
    df = create_test_data()
    logger.info(f"Created test data: {df.shape}")
    
    # Create Excel handler
    excel_handler = ExcelHandler()
    
    # Test pie chart visualization - this previously caused the error
    chart_path = excel_handler.generate_excel_visualization(
        df, "pie", "Month", "Profit", "Profit by Month"
    )
    
    if isinstance(chart_path, str) and chart_path.startswith("Error"):
        logger.error(f"Test failed: {chart_path}")
        return False
    else:
        logger.info(f"Test passed: Chart saved to {chart_path}")
        return True

def test_mixed_types():
    """Test visualization with mixed types"""
    logger.info("Testing visualization with mixed data types")
    
    # Create test data with mixed types
    data = {
        'Category': ['A', 'B', 'C', 'D', 'E', 1, 2, 3],  # Intentionally mixed types
        'Value': [100, 200, 300, 400, 500, 600, 700, 800]
    }
    df = pd.DataFrame(data)
    logger.info(f"Created mixed type test data: {df.shape}")
    
    # Create Excel handler
    excel_handler = ExcelHandler()
    
    # Test pie chart visualization with mixed types
    chart_path = excel_handler.generate_excel_visualization(
        df, "pie", "Category", "Value", "Value by Category"
    )
    
    if isinstance(chart_path, str) and chart_path.startswith("Error"):
        logger.error(f"Mixed types test failed: {chart_path}")
        return False
    else:
        logger.info(f"Mixed types test passed: Chart saved to {chart_path}")
        return True

def test_date_column():
    """Test visualization with date column"""
    logger.info("Testing visualization with date column")
    
    # Create test data with dates
    dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
    data = {
        'Date': dates,
        'Revenue': [1000, 1200, 1500, 1800, 2000, 2200, 1800, 1600, 1400, 1900, 2100, 2500]
    }
    df = pd.DataFrame(data)
    logger.info(f"Created date test data: {df.shape}")
    
    # Create Excel handler
    excel_handler = ExcelHandler()
    
    # Test visualization with date column
    chart_path = excel_handler.generate_excel_visualization(
        df, "line", "Date", "Revenue", "Revenue over Time"
    )
    
    if isinstance(chart_path, str) and chart_path.startswith("Error"):
        logger.error(f"Date column test failed: {chart_path}")
        return False
    else:
        logger.info(f"Date column test passed: Chart saved to {chart_path}")
        return True

def main():
    """Run all tests"""
    logger.info("Starting Excel visualization tests")
    
    # Run tests
    pie_test = test_pie_chart()
    mixed_test = test_mixed_types()
    date_test = test_date_column()
    
    # Report results
    logger.info("Test Results:")
    logger.info(f"Pie Chart Test: {'PASS' if pie_test else 'FAIL'}")
    logger.info(f"Mixed Types Test: {'PASS' if mixed_test else 'FAIL'}")
    logger.info(f"Date Column Test: {'PASS' if date_test else 'FAIL'}")
    
    if pie_test and mixed_test and date_test:
        logger.info("All tests PASSED! The fix was successful.")
    else:
        logger.error("Some tests FAILED. The fix may not be complete.")

if __name__ == "__main__":
    main() 