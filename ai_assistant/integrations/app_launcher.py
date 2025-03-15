"""
Application launcher integration for the AI Assistant.
"""

import os
import subprocess
import logging
import platform
import re
import winreg
import glob
from pathlib import Path

logger = logging.getLogger("ai_assistant")

class AppLauncher:
    """
    Application launcher integration for the AI Assistant.
    
    Provides functionality to find and launch applications on the system.
    """
    
    def __init__(self):
        """Initialize the application launcher."""
        self.system = platform.system()
        self.common_apps = self._get_common_apps()
        
    def _get_common_apps(self):
        """
        Get a dictionary of common applications and their executable names.
        
        Returns:
            dict: Dictionary mapping app names to executable names
        """
        common_apps = {
            # Browsers
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "mozilla firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "safari": "safari.exe",
            "opera": "opera.exe",
            "brave": "brave.exe",
            
            # Office
            "word": "winword.exe",
            "microsoft word": "winword.exe",
            "excel": "excel.exe",
            "microsoft excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "microsoft powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "microsoft outlook": "outlook.exe",
            "onenote": "onenote.exe",
            "microsoft onenote": "onenote.exe",
            "access": "msaccess.exe",
            "microsoft access": "msaccess.exe",
            
            # Development
            "visual studio": "devenv.exe",
            "vs code": "code.exe",
            "visual studio code": "code.exe",
            "notepad": "notepad.exe",
            "notepad++": "notepad++.exe",
            "sublime text": "sublime_text.exe",
            "atom": "atom.exe",
            "intellij": "idea64.exe",
            "pycharm": "pycharm64.exe",
            "eclipse": "eclipse.exe",
            "android studio": "studio64.exe",
            "git bash": "git-bash.exe",
            "terminal": "wt.exe",
            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            
            # Media
            "vlc": "vlc.exe",
            "windows media player": "wmplayer.exe",
            "spotify": "spotify.exe",
            "itunes": "itunes.exe",
            "netflix": "netflix.exe",
            "youtube": "youtube.exe",
            "zoom": "zoom.exe",
            "teams": "teams.exe",
            "microsoft teams": "teams.exe",
            "skype": "skype.exe",
            "discord": "discord.exe",
            "slack": "slack.exe",
            
            # Graphics
            "photoshop": "photoshop.exe",
            "adobe photoshop": "photoshop.exe",
            "illustrator": "illustrator.exe",
            "adobe illustrator": "illustrator.exe",
            "gimp": "gimp.exe",
            "paint": "mspaint.exe",
            "paint 3d": "paint3d.exe",
            
            # Utilities
            "calculator": "calc.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "settings": "ms-settings:",
            "snipping tool": "snippingtool.exe",
            "snip & sketch": "ScreenSketch.exe",
            
            # Games
            "steam": "steam.exe",
            "epic games": "epicgameslauncher.exe",
            "epic": "epicgameslauncher.exe",
            "origin": "origin.exe",
            "uplay": "uplay.exe",
            "battle.net": "battle.net.exe",
            "minecraft": "minecraft.exe"
        }
        
        # Add macOS specific apps if on macOS
        if self.system == "Darwin":
            mac_apps = {
                "safari": "Safari",
                "terminal": "Terminal",
                "finder": "Finder",
                "keynote": "Keynote",
                "pages": "Pages",
                "numbers": "Numbers",
                "preview": "Preview",
                "photos": "Photos",
                "music": "Music",
                "app store": "App Store",
                "system preferences": "System Preferences"
            }
            common_apps.update(mac_apps)
            
        # Add Linux specific apps if on Linux
        elif self.system == "Linux":
            linux_apps = {
                "terminal": "gnome-terminal",
                "nautilus": "nautilus",
                "files": "nautilus",
                "settings": "gnome-control-center",
                "software": "gnome-software"
            }
            common_apps.update(linux_apps)
            
        return common_apps
    
    def find_app_path(self, app_name):
        """
        Find the path to an application.
        
        Args:
            app_name (str): Name of the application to find
            
        Returns:
            str: Path to the application executable or None if not found
        """
        app_name = app_name.lower()
        
        # Check if it's a common app
        if app_name in self.common_apps:
            executable = self.common_apps[app_name]
            
            # For Windows settings app
            if executable == "ms-settings:":
                return executable
                
            # Try to find the executable
            if self.system == "Windows":
                # Check Program Files
                program_files_paths = [
                    os.environ.get("ProgramFiles", "C:\\Program Files"),
                    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                    os.environ.get("LocalAppData", "C:\\Users\\{}\\AppData\\Local".format(os.getenv("USERNAME"))),
                    os.environ.get("AppData", "C:\\Users\\{}\\AppData\\Roaming".format(os.getenv("USERNAME")))
                ]
                
                for base_path in program_files_paths:
                    for root, dirs, files in os.walk(base_path):
                        if executable in files:
                            return os.path.join(root, executable)
                
                # Check Windows Registry for installed applications
                try:
                    app_paths_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
                    for i in range(winreg.QueryInfoKey(app_paths_key)[0]):
                        app_key_name = winreg.EnumKey(app_paths_key, i)
                        if app_key_name.lower() == executable.lower():
                            app_key = winreg.OpenKey(app_paths_key, app_key_name)
                            app_path = winreg.QueryValueEx(app_key, "")[0]
                            return app_path
                except Exception as e:
                    logger.error(f"Error searching registry: {e}")
                
                # Check PATH environment
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_path = os.path.join(path, executable)
                    if os.path.isfile(exe_path):
                        return exe_path
                        
            elif self.system == "Darwin":  # macOS
                # Check Applications folder
                applications_path = "/Applications"
                app_bundle = f"{executable}.app"
                app_path = os.path.join(applications_path, app_bundle)
                if os.path.exists(app_path):
                    return app_path
                    
            elif self.system == "Linux":
                # Check common Linux executable paths
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_path = os.path.join(path, executable)
                    if os.path.isfile(exe_path):
                        return exe_path
        
        # If not found in common apps, try to find by name
        if self.system == "Windows":
            # Search Start Menu
            start_menu_paths = [
                os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
                os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
            ]
            
            for start_menu in start_menu_paths:
                # Look for .lnk files
                for root, dirs, files in os.walk(start_menu):
                    for file in files:
                        if file.lower().endswith(".lnk") and app_name.lower() in file.lower():
                            return os.path.join(root, file)
            
            # Try to find executable directly
            program_files_paths = [
                os.environ.get("ProgramFiles", "C:\\Program Files"),
                os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            ]
            
            for base_path in program_files_paths:
                # Search for folders matching the app name
                app_dirs = glob.glob(f"{base_path}\\*{app_name}*", recursive=False)
                for app_dir in app_dirs:
                    # Look for .exe files in the directory
                    exe_files = glob.glob(f"{app_dir}\\*.exe", recursive=True)
                    if exe_files:
                        return exe_files[0]
                        
            # Check Windows Registry for installed applications
            try:
                uninstall_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    try:
                        app_key_name = winreg.EnumKey(uninstall_key, i)
                        app_key = winreg.OpenKey(uninstall_key, app_key_name)
                        display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                        
                        if app_name.lower() in display_name.lower():
                            try:
                                install_location = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                if install_location:
                                    # Look for .exe files in the install location
                                    exe_files = glob.glob(f"{install_location}\\*.exe", recursive=True)
                                    if exe_files:
                                        return exe_files[0]
                            except:
                                pass
                    except:
                        continue
            except Exception as e:
                logger.error(f"Error searching registry: {e}")
                
        elif self.system == "Darwin":  # macOS
            # Check Applications folder for app bundles containing the app name
            applications_path = "/Applications"
            for app_bundle in os.listdir(applications_path):
                if app_bundle.lower().endswith(".app") and app_name.lower() in app_bundle.lower():
                    return os.path.join(applications_path, app_bundle)
                    
        elif self.system == "Linux":
            # Check for .desktop files
            desktop_paths = [
                os.path.expanduser("~/.local/share/applications"),
                "/usr/share/applications",
                "/usr/local/share/applications"
            ]
            
            for desktop_path in desktop_paths:
                if os.path.exists(desktop_path):
                    for file in os.listdir(desktop_path):
                        if file.lower().endswith(".desktop") and app_name.lower() in file.lower():
                            return os.path.join(desktop_path, file)
        
        return None
    
    def launch_app(self, app_name):
        """
        Launch an application.
        
        Args:
            app_name (str): Name of the application to launch
            
        Returns:
            str: Success message or error message
        """
        try:
            # Special case for URLs (websites)
            if app_name.lower().startswith(("http://", "https://", "www.")):
                if app_name.lower().startswith("www."):
                    app_name = "https://" + app_name
                    
                if self.system == "Windows":
                    os.startfile(app_name)
                elif self.system == "Darwin":  # macOS
                    subprocess.Popen(["open", app_name])
                else:  # Linux
                    subprocess.Popen(["xdg-open", app_name])
                    
                return f"Opened website: {app_name}"
            
            # Special case for Windows settings
            if app_name.lower() == "settings" and self.system == "Windows":
                subprocess.Popen(["start", "ms-settings:"], shell=True)
                return "Opened Windows Settings"
                
            # Find the application path
            app_path = self.find_app_path(app_name)
            
            if not app_path:
                return f"Could not find application: {app_name}"
                
            # Launch the application
            if self.system == "Windows":
                if app_path.lower().endswith(".lnk"):
                    # Launch shortcut
                    os.startfile(app_path)
                else:
                    # Launch executable
                    subprocess.Popen([app_path])
            elif self.system == "Darwin":  # macOS
                if app_path.endswith(".app"):
                    # Launch app bundle
                    subprocess.Popen(["open", app_path])
                else:
                    # Launch executable
                    subprocess.Popen([app_path])
            else:  # Linux
                if app_path.endswith(".desktop"):
                    # Launch desktop file
                    subprocess.Popen(["gtk-launch", os.path.basename(app_path)])
                else:
                    # Launch executable
                    subprocess.Popen([app_path])
                    
            return f"Launched application: {app_name}"
            
        except Exception as e:
            logger.error(f"Error launching application: {e}")
            return f"Error launching application: {str(e)}"
    
    def list_installed_apps(self, limit=20):
        """
        List installed applications on the system.
        
        Args:
            limit (int): Maximum number of applications to list
            
        Returns:
            str: Formatted list of installed applications
        """
        installed_apps = []
        
        try:
            if self.system == "Windows":
                # Get apps from Start Menu
                start_menu_paths = [
                    os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
                    os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
                ]
                
                for start_menu in start_menu_paths:
                    for root, dirs, files in os.walk(start_menu):
                        for file in files:
                            if file.lower().endswith(".lnk"):
                                app_name = os.path.splitext(file)[0]
                                if app_name not in installed_apps:
                                    installed_apps.append(app_name)
                
                # Get apps from Registry
                try:
                    uninstall_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                    for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                        try:
                            app_key_name = winreg.EnumKey(uninstall_key, i)
                            app_key = winreg.OpenKey(uninstall_key, app_key_name)
                            display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                            
                            if display_name and display_name not in installed_apps:
                                installed_apps.append(display_name)
                        except:
                            continue
                except Exception as e:
                    logger.error(f"Error reading registry: {e}")
                    
            elif self.system == "Darwin":  # macOS
                # Get apps from Applications folder
                applications_path = "/Applications"
                for app_bundle in os.listdir(applications_path):
                    if app_bundle.lower().endswith(".app"):
                        app_name = os.path.splitext(app_bundle)[0]
                        installed_apps.append(app_name)
                        
            elif self.system == "Linux":
                # Get apps from .desktop files
                desktop_paths = [
                    os.path.expanduser("~/.local/share/applications"),
                    "/usr/share/applications",
                    "/usr/local/share/applications"
                ]
                
                for desktop_path in desktop_paths:
                    if os.path.exists(desktop_path):
                        for file in os.listdir(desktop_path):
                            if file.lower().endswith(".desktop"):
                                app_name = os.path.splitext(file)[0]
                                installed_apps.append(app_name)
            
            # Sort and limit the list
            installed_apps = sorted(installed_apps)
            if limit > 0:
                installed_apps = installed_apps[:limit]
                
            # Format the output
            result = "📱 Installed Applications:\n\n"
            for app in installed_apps:
                result += f"• {app}\n"
                
            if limit > 0 and len(installed_apps) == limit:
                result += f"\nShowing {limit} applications. There may be more installed."
                
            return result
            
        except Exception as e:
            logger.error(f"Error listing installed applications: {e}")
            return f"Error listing installed applications: {str(e)}" 