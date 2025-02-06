"""
Module cache system for CoreSecurityFramework
"""
import json
import time
from pathlib import Path
import requests
import base64
import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from .colors import Colors

class ModuleCache:
    CACHE_FILE = Path(__file__).parent.parent / 'cache' / 'modules_cache.json'
    CACHE_DURATION = timedelta(hours=12)

    @classmethod
    def needs_update(cls) -> bool:
        """Check if cache needs to be updated"""
        if not cls.CACHE_FILE.exists():
            return True
            
        try:
            with open(cls.CACHE_FILE) as f:
                cache = json.load(f)
                last_update = datetime.fromisoformat(cache.get('last_update', '2000-01-01'))
                return datetime.now() - last_update > cls.CACHE_DURATION
        except:
            return True

    @classmethod
    def _fetch_repo_contents(cls, api_url: str, path: str = "", headers: dict = None) -> List[dict]:
        """Recursively fetch repository contents including subdirectories"""
        contents = []
        current_url = f"{api_url}/{path}".rstrip('/')
        
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            
            for item in response.json():
                if item["type"] == "dir":
                    # Recursively fetch contents of subdirectory
                    contents.extend(cls._fetch_repo_contents(api_url, item["path"], headers))
                elif item["type"] == "file" and item["name"].endswith(".py"):
                    # Add file details to contents
                    contents.append({
                        "path": item["path"],  # Include full path from repo root
                        "name": item["name"],
                        "url": item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                    })
                    
            return contents
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error fetching repository contents: {e}{Colors.ENDC}")
            return contents

    @classmethod
    def update_cache(cls, repo_url: str) -> bool:
        """Update modules cache from repository"""
        try:
            print(f"{Colors.CYAN}[*] Updating modules cache...{Colors.ENDC}")
            
            # Create cache directory if needed
            cls.CACHE_FILE.parent.mkdir(exist_ok=True)
            
            # Convert GitHub URL to API URL
            api_url = repo_url.replace("github.com", "api.github.com/repos")
            if api_url.endswith("/"):
                api_url = api_url[:-1]
            api_url += "/contents"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CoreSecFrame-ModuleCache"
            }
            
            # Fetch all repository contents recursively
            modules = []
            contents = cls._fetch_repo_contents(api_url, headers=headers)
            
            for item in contents:
                try:
                    # Get file content to parse metadata
                    file_response = requests.get(item["url"], headers=headers)
                    content = file_response.text
                    
                    # Parse module info
                    name = item["name"].replace(".py", "")
                    description, category = cls._parse_module_info(content)
                    
                    # If category not explicitly defined, use directory name
                    if category == "Uncategorized" and "/" in item["path"]:
                        category = item["path"].split("/")[0]
                    
                    modules.append({
                        "name": name,
                        "description": description,
                        "category": category,
                        "url": item["url"],
                        "filename": item["name"],
                        "path": item["path"]  # Store full path for correct loading
                    })
                    
                    # Add delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"{Colors.WARNING}[!] Error processing module {item['name']}: {e}{Colors.ENDC}")
                    continue
            
            # Save to cache file
            cache_data = {
                "last_update": datetime.now().isoformat(),
                "modules": modules
            }
            
            with open(cls.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=4)
                
            print(f"{Colors.GREEN}[✓] Cache updated successfully{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error updating cache: {e}{Colors.ENDC}")
            return False

    @classmethod
    def get_cached_modules(cls) -> list:
        """Get modules from cache"""
        try:
            if not cls.CACHE_FILE.exists():
                return []
                
            with open(cls.CACHE_FILE) as f:
                cache = json.load(f)
                return cache.get('modules', [])
        except:
            return []

    @classmethod
    def _parse_module_info(cls, content: str) -> tuple:
        """Parse module metadata from content"""
        description = "No description"
        category = "Uncategorized"
        
        try:
            # Look for category in _get_category()
            if "_get_category" in content:
                cat_match = re.search(r'def\s+_get_category.*?return\s+[\'"](.+?)[\'"]', content, re.DOTALL)
                if cat_match:
                    category = cat_match.group(1)
            
            # Look for description in _get_description() or docstring
            if "_get_description" in content:
                desc_match = re.search(r'def\s+_get_description.*?return\s+[\'"](.+?)[\'"]', content, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1)
            elif '"""' in content:
                doc_start = content.find('"""') + 3
                doc_end = content.find('"""', doc_start)
                if doc_end > doc_start:
                    description = content[doc_start:doc_end].strip().split('\n')[0]
                    
        except Exception:
            pass
            
        return description, category