"""
GitHub integration for the AI Assistant.
"""

import os
import logging
import base64
import json
import requests
from datetime import datetime
import re

logger = logging.getLogger("ai_assistant")

class GitHubIntegration:
    """
    GitHub integration for the AI Assistant.
    
    Attributes:
        token (str): GitHub personal access token
        username (str): GitHub username
        api_base (str): GitHub API base URL
    """
    
    def __init__(self):
        """Initialize the GitHub integration."""
        self.token = None
        self.username = None
        self.api_base = "https://api.github.com"
        self.authenticated = False
        
        # Try to load token from environment
        self._load_token()
        
        # Log status
        if self.authenticated:
            logger.info(f"GitHub integration initialized and authenticated as {self.username}")
        else:
            logger.info("GitHub integration initialized but not authenticated")
        
    def _load_token(self):
        """Load GitHub token from environment or config file."""
        self.token = os.getenv("GITHUB_TOKEN")
        if self.token:
            self.authenticate(self.token)
        
    def save_token(self, token):
        """
        Save GitHub token to environment variable.
        
        Args:
            token (str): GitHub personal access token
            
        Returns:
            bool: True if token was saved successfully
        """
        try:
            os.environ["GITHUB_TOKEN"] = token
            return True
        except Exception as e:
            logger.error(f"Error saving GitHub token: {e}")
            return False
        
    def authenticate(self, token=None):
        """
        Authenticate with GitHub API.
        
        Args:
            token (str, optional): GitHub personal access token
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Use provided token or try to get from environment
            self.token = token or self.token
            
            if not self.token:
                logger.error("GitHub token not found")
                return False
                
            # Test the token by getting user info
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(f"{self.api_base}/user", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                self.username = user_data["login"]
                self.authenticated = True
                logger.info(f"Authenticated with GitHub as {self.username}")
                return True
            else:
                logger.error(f"GitHub authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"GitHub authentication error: {e}")
            return False
    
    def list_repositories(self, limit=10):
        """
        List user's repositories.
        
        Args:
            limit (int): Maximum number of repositories to retrieve
            
        Returns:
            str: Formatted list of repositories or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                f"{self.api_base}/user/repos?sort=updated&per_page={limit}",
                headers=headers
            )
            
            if response.status_code == 200:
                repos = response.json()
                
                if not repos:
                    return "No repositories found."
                    
                result = "📚 Your GitHub repositories:\n\n"
                for repo in repos:
                    updated_at = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
                    updated_str = updated_at.strftime("%Y-%m-%d %H:%M")
                    
                    result += f"• {repo['name']}\n"
                    result += f"  URL: {repo['html_url']}\n"
                    result += f"  Description: {repo['description'] or 'No description'}\n"
                    result += f"  Last updated: {updated_str}\n"
                    result += f"  Stars: {repo['stargazers_count']}\n\n"
                    
                return result
            else:
                return f"Error listing repositories: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error listing GitHub repositories: {e}")
            return f"Error listing repositories: {str(e)}"
    
    def create_repository(self, name, description=None, private=False):
        """
        Create a new GitHub repository.
        
        Args:
            name (str): Repository name
            description (str, optional): Repository description
            private (bool, optional): Whether the repository should be private
            
        Returns:
            str: Success message with repository URL or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "name": name,
                "private": private
            }
            
            if description:
                data["description"] = description
                
            response = requests.post(
                f"{self.api_base}/user/repos",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                repo_data = response.json()
                return f"✅ Repository created successfully: {repo_data['html_url']}"
            else:
                error_msg = response.json().get("message", f"Status code: {response.status_code}")
                return f"Error creating repository: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating GitHub repository: {e}")
            return f"Error creating repository: {str(e)}"
    
    def create_issue(self, repo, title, body=None, labels=None):
        """
        Create a new issue in a repository.
        
        Args:
            repo (str): Repository name (format: username/repo or just repo)
            title (str): Issue title
            body (str, optional): Issue description
            labels (list, optional): List of label names
            
        Returns:
            str: Success message with issue URL or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            # Format repository name
            if "/" not in repo:
                repo = f"{self.username}/{repo}"
                
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": title
            }
            
            if body:
                data["body"] = body
                
            if labels:
                data["labels"] = labels
                
            response = requests.post(
                f"{self.api_base}/repos/{repo}/issues",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                issue_data = response.json()
                return f"✅ Issue created successfully: {issue_data['html_url']}"
            else:
                error_msg = response.json().get("message", f"Status code: {response.status_code}")
                return f"Error creating issue: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return f"Error creating issue: {str(e)}"
    
    def list_issues(self, repo, state="open", limit=10):
        """
        List issues in a repository.
        
        Args:
            repo (str): Repository name (format: username/repo or just repo)
            state (str, optional): Issue state (open, closed, all)
            limit (int, optional): Maximum number of issues to retrieve
            
        Returns:
            str: Formatted list of issues or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            # Format repository name
            if "/" not in repo:
                repo = f"{self.username}/{repo}"
                
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                f"{self.api_base}/repos/{repo}/issues?state={state}&per_page={limit}",
                headers=headers
            )
            
            if response.status_code == 200:
                issues = response.json()
                
                if not issues:
                    return f"No {state} issues found in {repo}."
                    
                result = f"📝 {state.capitalize()} issues in {repo}:\n\n"
                for issue in issues:
                    created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                    created_str = created_at.strftime("%Y-%m-%d")
                    
                    result += f"• #{issue['number']}: {issue['title']}\n"
                    result += f"  URL: {issue['html_url']}\n"
                    result += f"  Created: {created_str}\n"
                    
                    if issue.get("labels"):
                        labels = ", ".join([label["name"] for label in issue["labels"]])
                        result += f"  Labels: {labels}\n"
                        
                    result += "\n"
                    
                return result
            else:
                error_msg = response.json().get("message", f"Status code: {response.status_code}")
                return f"Error listing issues: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error listing GitHub issues: {e}")
            return f"Error listing issues: {str(e)}"
    
    def create_file(self, repo, path, content, message):
        """
        Create or update a file in a repository.
        
        Args:
            repo (str): Repository name (format: username/repo or just repo)
            path (str): File path in the repository
            content (str): File content
            message (str): Commit message
            
        Returns:
            str: Success message or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            # Format repository name
            if "/" not in repo:
                repo = f"{self.username}/{repo}"
                
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Check if file exists to get the SHA
            sha = None
            response = requests.get(
                f"{self.api_base}/repos/{repo}/contents/{path}",
                headers=headers
            )
            
            if response.status_code == 200:
                sha = response.json().get("sha")
                
            # Prepare the data for creating/updating the file
            data = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode()
            }
            
            if sha:
                data["sha"] = sha
                
            response = requests.put(
                f"{self.api_base}/repos/{repo}/contents/{path}",
                headers=headers,
                json=data
            )
            
            if response.status_code in (200, 201):
                file_data = response.json()
                action = "updated" if sha else "created"
                return f"✅ File {action} successfully: {file_data['content']['html_url']}"
            else:
                error_msg = response.json().get("message", f"Status code: {response.status_code}")
                return f"Error creating/updating file: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error creating/updating GitHub file: {e}")
            return f"Error creating/updating file: {str(e)}"
    
    def delete_repository(self, repo):
        """
        Delete a GitHub repository.
        
        Args:
            repo (str): Repository name (format: username/repo or just repo)
            
        Returns:
            str: Success message or error message
        """
        if not self.authenticated and not self.authenticate():
            return "Not authenticated with GitHub. Please set up authentication first."
            
        try:
            # Format repository name
            if "/" not in repo:
                repo = f"{self.username}/{repo}"
                
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Delete repository
            response = requests.delete(
                f"{self.api_base}/repos/{repo}",
                headers=headers
            )
            
            if response.status_code == 204:
                return f"✅ Repository '{repo}' deleted successfully."
            else:
                error_msg = ""
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"Status code: {response.status_code}")
                except:
                    error_msg = f"Status code: {response.status_code}"
                
                return f"Error deleting repository: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error deleting GitHub repository: {e}")
            return f"Error deleting repository: {str(e)}" 