"""
File Explorer integration for the AI Assistant.
"""

import os
import shutil
import logging
import glob
import datetime
import zipfile
import send2trash
from pathlib import Path

logger = logging.getLogger("ai_assistant")

class FileExplorer:
    """
    File Explorer integration for the AI Assistant.
    
    Provides file system operations like listing, creating, deleting,
    and moving files and directories.
    """
    
    def __init__(self):
        """Initialize the File Explorer integration."""
        self.current_dir = os.getcwd()
        
    def get_current_directory(self):
        """
        Get the current working directory.
        
        Returns:
            str: Current directory path
        """
        return self.current_dir
        
    def set_current_directory(self, path):
        """
        Set the current working directory.
        
        Args:
            path (str): Directory path to set as current
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: Directory '{path}' does not exist."
                
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory."
                
            os.chdir(path)
            self.current_dir = path
            return f"Current directory changed to: {path}"
            
        except Exception as e:
            logger.error(f"Error changing directory: {e}")
            return f"Error changing directory: {str(e)}"
    
    def list_directory(self, path=None, pattern="*", show_hidden=False):
        """
        List contents of a directory.
        
        Args:
            path (str, optional): Directory path to list
            pattern (str, optional): File pattern to match
            show_hidden (bool, optional): Whether to show hidden files
            
        Returns:
            str: Formatted directory listing
        """
        try:
            # Use current directory if path not provided
            if not path:
                path = self.current_dir
                
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: Directory '{path}' does not exist."
                
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory."
                
            # Get directory contents
            search_pattern = os.path.join(path, pattern)
            items = glob.glob(search_pattern)
            
            # Filter hidden files if needed
            if not show_hidden:
                items = [item for item in items if not os.path.basename(item).startswith('.')]
                
            # Sort items (directories first, then files)
            dirs = [item for item in items if os.path.isdir(item)]
            files = [item for item in items if os.path.isfile(item)]
            
            dirs.sort()
            files.sort()
            
            # Format the output
            result = f"📂 Contents of {path}:\n\n"
            
            if not dirs and not files:
                result += "Directory is empty."
                return result
                
            # Add directories
            if dirs:
                result += "Directories:\n"
                for dir_path in dirs:
                    dir_name = os.path.basename(dir_path)
                    result += f"  📁 {dir_name}\n"
                result += "\n"
                
            # Add files
            if files:
                result += "Files:\n"
                for file_path in files:
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                        
                    result += f"  📄 {file_name} ({size_str}, {mod_time_str})\n"
                    
            return result
            
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            return f"Error listing directory: {str(e)}"
    
    def create_directory(self, path):
        """
        Create a new directory.
        
        Args:
            path (str): Directory path to create
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if os.path.exists(path):
                return f"Error: '{path}' already exists."
                
            os.makedirs(path)
            return f"Directory created: {path}"
            
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return f"Error creating directory: {str(e)}"
    
    def delete_item(self, path, use_trash=True):
        """
        Delete a file or directory.
        
        Args:
            path (str): Path to delete
            use_trash (bool, optional): Whether to move to trash instead of permanent deletion
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: '{path}' does not exist."
                
            # Get item type for the message
            item_type = "directory" if os.path.isdir(path) else "file"
                
            # Delete the item
            if use_trash:
                send2trash.send2trash(path)
                return f"{item_type.capitalize()} moved to trash: {path}"
            else:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return f"{item_type.capitalize()} permanently deleted: {path}"
                
        except Exception as e:
            logger.error(f"Error deleting item: {e}")
            return f"Error deleting item: {str(e)}"
    
    def move_item(self, source, destination):
        """
        Move a file or directory.
        
        Args:
            source (str): Source path
            destination (str): Destination path
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
                
            if not os.path.isabs(destination):
                destination = os.path.join(self.current_dir, destination)
                
            # Normalize paths
            source = os.path.normpath(source)
            destination = os.path.normpath(destination)
                
            if not os.path.exists(source):
                return f"Error: Source '{source}' does not exist."
                
            # Get item type for the message
            item_type = "directory" if os.path.isdir(source) else "file"
                
            # Move the item
            shutil.move(source, destination)
            return f"{item_type.capitalize()} moved: {source} -> {destination}"
            
        except Exception as e:
            logger.error(f"Error moving item: {e}")
            return f"Error moving item: {str(e)}"
    
    def copy_item(self, source, destination):
        """
        Copy a file or directory.
        
        Args:
            source (str): Source path
            destination (str): Destination path
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
                
            if not os.path.isabs(destination):
                destination = os.path.join(self.current_dir, destination)
                
            # Normalize paths
            source = os.path.normpath(source)
            destination = os.path.normpath(destination)
                
            if not os.path.exists(source):
                return f"Error: Source '{source}' does not exist."
                
            # Copy the item
            if os.path.isdir(source):
                shutil.copytree(source, destination)
                return f"Directory copied: {source} -> {destination}"
            else:
                shutil.copy2(source, destination)
                return f"File copied: {source} -> {destination}"
                
        except Exception as e:
            logger.error(f"Error copying item: {e}")
            return f"Error copying item: {str(e)}"
    
    def rename_item(self, path, new_name):
        """
        Rename a file or directory.
        
        Args:
            path (str): Path to rename
            new_name (str): New name (not full path)
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: '{path}' does not exist."
                
            # Get parent directory
            parent_dir = os.path.dirname(path)
            
            # Create new path
            new_path = os.path.join(parent_dir, new_name)
            
            if os.path.exists(new_path):
                return f"Error: '{new_path}' already exists."
                
            # Get item type for the message
            item_type = "directory" if os.path.isdir(path) else "file"
                
            # Rename the item
            os.rename(path, new_path)
            return f"{item_type.capitalize()} renamed: {path} -> {new_path}"
            
        except Exception as e:
            logger.error(f"Error renaming item: {e}")
            return f"Error renaming item: {str(e)}"
    
    def create_file(self, path, content=""):
        """
        Create a new file with optional content.
        
        Args:
            path (str): File path to create
            content (str, optional): Content to write to the file
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if os.path.exists(path):
                return f"Error: '{path}' already exists."
                
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
                
            # Create the file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return f"File created: {path}"
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return f"Error creating file: {str(e)}"
    
    def read_file(self, path, max_size=10240):
        """
        Read the contents of a file.
        
        Args:
            path (str): File path to read
            max_size (int, optional): Maximum file size to read in bytes
            
        Returns:
            str: File contents or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: '{path}' does not exist."
                
            if not os.path.isfile(path):
                return f"Error: '{path}' is not a file."
                
            # Check file size
            file_size = os.path.getsize(path)
            if file_size > max_size:
                return f"Error: File is too large ({file_size} bytes). Maximum size is {max_size} bytes."
                
            # Read the file
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            return f"📄 Contents of {path}:\n\n{content}"
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return f"Error reading file: {str(e)}"
    
    def search_files(self, pattern, path=None, content_search=None):
        """
        Search for files by name pattern and optionally by content.
        
        Args:
            pattern (str): File name pattern to search for
            path (str, optional): Directory to search in
            content_search (str, optional): Text to search for in files
            
        Returns:
            str: Search results or error message
        """
        try:
            # Use current directory if path not provided
            if not path:
                path = self.current_dir
                
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)
                
            # Normalize path
            path = os.path.normpath(path)
                
            if not os.path.exists(path):
                return f"Error: Directory '{path}' does not exist."
                
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory."
                
            # Search for files matching the pattern
            search_pattern = os.path.join(path, "**", pattern)
            matching_files = glob.glob(search_pattern, recursive=True)
            
            # Filter to only files (not directories)
            matching_files = [f for f in matching_files if os.path.isfile(f)]
            
            if not matching_files:
                return f"No files matching '{pattern}' found in {path}."
                
            # If content search is specified, filter files by content
            if content_search:
                content_matches = []
                
                for file_path in matching_files:
                    try:
                        # Skip binary files and very large files
                        if os.path.getsize(file_path) > 1024 * 1024:  # 1 MB
                            continue
                            
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if content_search.lower() in content.lower():
                            content_matches.append(file_path)
                    except:
                        # Skip files that can't be read as text
                        continue
                        
                matching_files = content_matches
                
                if not matching_files:
                    return f"No files containing '{content_search}' found."
            
            # Format the results
            result = f"🔍 Search results for '{pattern}'"
            if content_search:
                result += f" containing '{content_search}'"
            result += f" in {path}:\n\n"
            
            for file_path in matching_files:
                file_size = os.path.getsize(file_path)
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    
                result += f"📄 {file_path} ({size_str}, {mod_time_str})\n"
                
            return result
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return f"Error searching files: {str(e)}"
    
    def zip_items(self, output_path, items):
        """
        Create a zip archive of files and directories.
        
        Args:
            output_path (str): Path for the output zip file
            items (list): List of paths to include in the zip
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(output_path):
                output_path = os.path.join(self.current_dir, output_path)
                
            # Normalize output path
            output_path = os.path.normpath(output_path)
            
            # Add .zip extension if not present
            if not output_path.lower().endswith('.zip'):
                output_path += '.zip'
                
            # Process items
            processed_items = []
            for item in items:
                # Handle relative paths
                if not os.path.isabs(item):
                    item = os.path.join(self.current_dir, item)
                    
                # Normalize path
                item = os.path.normpath(item)
                
                if not os.path.exists(item):
                    return f"Error: '{item}' does not exist."
                    
                processed_items.append(item)
                
            # Create the zip file
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in processed_items:
                    if os.path.isfile(item):
                        # Add file to zip
                        zipf.write(item, os.path.basename(item))
                    elif os.path.isdir(item):
                        # Add directory contents to zip
                        for root, _, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(item))
                                zipf.write(file_path, arcname)
                                
            return f"Zip archive created: {output_path}"
            
        except Exception as e:
            logger.error(f"Error creating zip archive: {e}")
            return f"Error creating zip archive: {str(e)}"
    
    def unzip_file(self, zip_path, extract_path=None):
        """
        Extract a zip archive.
        
        Args:
            zip_path (str): Path to the zip file
            extract_path (str, optional): Path to extract to
            
        Returns:
            str: Success message or error message
        """
        try:
            # Handle relative paths
            if not os.path.isabs(zip_path):
                zip_path = os.path.join(self.current_dir, zip_path)
                
            # Normalize zip path
            zip_path = os.path.normpath(zip_path)
            
            if not os.path.exists(zip_path):
                return f"Error: '{zip_path}' does not exist."
                
            if not os.path.isfile(zip_path):
                return f"Error: '{zip_path}' is not a file."
                
            if not zipfile.is_zipfile(zip_path):
                return f"Error: '{zip_path}' is not a valid zip file."
                
            # Use default extract path if not provided
            if not extract_path:
                extract_path = os.path.splitext(zip_path)[0]
                
            # Handle relative paths for extract path
            if not os.path.isabs(extract_path):
                extract_path = os.path.join(self.current_dir, extract_path)
                
            # Normalize extract path
            extract_path = os.path.normpath(extract_path)
            
            # Create extract directory if it doesn't exist
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
                
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_path)
                
            return f"Zip archive extracted to: {extract_path}"
            
        except Exception as e:
            logger.error(f"Error extracting zip archive: {e}")
            return f"Error extracting zip archive: {str(e)}" 