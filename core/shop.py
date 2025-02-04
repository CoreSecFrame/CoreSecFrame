"""
Shop module for downloading modules from GitHub repositories
"""
import os
import sys
import re
import textwrap
import requests
import base64
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Set
from .colors import Colors
from .base import ToolModule

@dataclass
class RemoteModule:
    """Class to store remote module information"""
    name: str
    description: str
    category: str
    url: str
    downloaded: bool = False

class ModuleShop:
    def __init__(self, repo_url: str, framework=None):
        self.repo_url = repo_url.replace("github.com", "api.github.com/repos")
        if self.repo_url.endswith("/"):
            self.repo_url = self.repo_url[:-1]
        self.repo_url += "/contents"
        self.modules: Dict[str, RemoteModule] = {}
        self.modules_dir = Path(__file__).parent.parent / 'modules'
        self.framework = framework
        self._fetch_modules()

    def _fetch_modules(self) -> None:
            """Fetch all modules from cache"""
            try:
                from .module_cache import ModuleCache
                cached_modules = ModuleCache.get_cached_modules()
                
                modules_dir = Path(__file__).parent.parent / 'modules'
                
                for module in cached_modules:
                    name = module["name"]
                    self.modules[name.lower()] = RemoteModule(
                        name=name,
                        description=module["description"],
                        category=module["category"],
                        url=module["url"],
                        downloaded=(modules_dir / module["filename"]).exists()
                    )
                    
            except Exception as e:
                print(f"{Colors.FAIL}[!] Error loading modules: {e}{Colors.ENDC}")
                sys.exit(1)

    def _parse_module_info(self, content: str) -> tuple:
        """
        Parse module content to extract metadata
        Returns: tuple (description, category)
        """
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
                    
        except Exception as e:
            print(f"{Colors.WARNING}[!] Error parsing module content: {e}{Colors.ENDC}")
            
        return description, category

    def download_module(self, module_name: str) -> bool:
        """Download a module to the modules directory"""
        module = self.modules.get(module_name.lower())
        if not module:
            print(f"{Colors.FAIL}[!] Module not found: {module_name}{Colors.ENDC}")
            return False
            
        if module.downloaded:
            print(f"{Colors.WARNING}[!] Module already downloaded{Colors.ENDC}")
            return True

        try:
            # Create modules directory if needed
            self.modules_dir.mkdir(parents=True, exist_ok=True)
            
            # Download module
            response = requests.get(module.url)
            response.raise_for_status()
            
            # Save module
            module_path = self.modules_dir / f"{module.name}.py"
            with open(module_path, 'wb') as f:
                f.write(response.content)
            
            # Create __init__.py if needed
            init_file = self.modules_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                
            module.downloaded = True
            print(f"{Colors.GREEN}[✓] Module downloaded successfully{Colors.ENDC}")

            # Reload modules in the framework
            print(f"{Colors.CYAN}[*] Reloading framework modules...{Colors.ENDC}")
            from .base import ToolModule
            self.framework.modules = ToolModule.load_modules(initial_load=False)
            print(f"{Colors.GREEN}[✓] Modules reloaded successfully{Colors.ENDC}")

            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error downloading module: {e}{Colors.ENDC}")
            return False

    def _calculate_description_width(self, modules: List[RemoteModule]) -> int:
        """Calculate optimal description width"""
        max_desc_length = max(len(module.description) for module in modules)
        return min(max(max_desc_length, 33), 60)

    def _create_table_border(self, desc_width: int, border_char: str) -> str:
        """Create table border line"""
        return f"{Colors.CYAN}{border_char}{'═'*18}{border_char}{'═'*17}{border_char}{'═'*(desc_width+2)}{border_char}{'═'*18}{border_char}"

    def _create_separator_line(self, desc_width: int) -> str:
        """Create table separator line"""
        return f"{Colors.CYAN}╟{'─'*18}╫{'─'*17}╫{'─'*(desc_width+2)}╫{'─'*18}╢"

    def _display_modules_table(self, modules_to_show: List[RemoteModule], page: int = 1, items_per_page: int = 5) -> None:
        """Display modules in a paginated table"""
        if not modules_to_show:
            print(f"{Colors.WARNING}[!] No modules were found{Colors.ENDC}")
            return
        total_items = len(modules_to_show)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        if page > total_pages:
            page = total_pages
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        # Get current page's modules
        current_modules = modules_to_show[start_idx:end_idx]
        # Calculate description width for current page
        desc_width = self._calculate_description_width(current_modules)
        # Draw table header
        print(self._create_table_border(desc_width, "╔"))
        print(f"{Colors.CYAN}║ {Colors.ACCENT}{'Name':<16} {Colors.CYAN}║", end='')
        print(f" {Colors.ACCENT}{'Status':<15} {Colors.CYAN}║", end='')
        print(f" {Colors.ACCENT}{'Description':<{desc_width}} {Colors.CYAN}║", end='')
        print(f" {Colors.ACCENT}{'Category':<16} {Colors.CYAN}║")
        print(self._create_table_border(desc_width, "╠"))
        # Draw module rows
        for i, module in enumerate(current_modules):
            status = f"{Colors.GREEN}Downloaded {Colors.ENDC}" if module.downloaded else f"{Colors.WARNING}Not Downloaded {Colors.ENDC}"
            # First line with all columns
            print(f"{Colors.CYAN}║ {Colors.TEXT}{module.name:<16} {Colors.CYAN}║", end='')
            print(f" {status:<24}{Colors.CYAN} ║", end='')
            # Handle multiline descriptions
            desc_lines = textwrap.wrap(module.description, desc_width)
            if not desc_lines:
                desc_lines = ['']
            # First line of description
            print(f" {Colors.TEXT}{desc_lines[0]:<{desc_width}} {Colors.CYAN}║", end='')
            print(f" {Colors.TEXT}{module.category:<16} {Colors.CYAN}║")
            # Additional description lines
            for line in desc_lines[1:]:
                print(f"{Colors.CYAN}║ {' '*16} ║ {' '*15} ║", end='')
                print(f" {Colors.TEXT}{line:<{desc_width}} {Colors.CYAN}║", end='')
                print(f" {' '*16} ║")
            # Separator between modules
            if i < len(current_modules) - 1:
                print(self._create_separator_line(desc_width))
        # Table footer
        print(self._create_table_border(desc_width, "╚"))
        
        # Show pagination info
        if total_pages > 1:
            print(f"\n{Colors.WARNING}Page {page}/{total_pages} ({total_items} total modules){Colors.ENDC}")
            print(f"{Colors.TEXT}Use 'n' for next page, 'p' for previous, any other key to exit{Colors.ENDC}")
            key = input().lower()
            if key == 'n' and page < total_pages:
                self._display_modules_table(modules_to_show, page + 1, items_per_page)
            elif key == 'p' and page > 1:
                self._display_modules_table(modules_to_show, page - 1, items_per_page)

    def show_category(self, category: str = None) -> None:
        """Display modules in a category"""
        if category == "category":
            # Show all categories
            categories = {module.category for module in self.modules.values()}
            print(f"\n{Colors.SUCCESS}[*] Available categories:{Colors.ENDC}")
            for cat in sorted(categories):
                count = sum(1 for m in self.modules.values() if m.category.lower() == cat.lower())
                print(f"{Colors.CYAN}[+] {cat}: {count} modules{Colors.ENDC}")
            return
            
        # Show modules in category
        modules = [
            module for module in self.modules.values()
            if not category or module.category.lower() == category.lower()
        ]
        
        if category:
            print(f"\n{Colors.CYAN}[*] Modules in category '{category}':{Colors.ENDC}")
        else:
            print(f"\n{Colors.CYAN}[*] All modules:{Colors.ENDC}")
            
        self._display_modules_table(modules)

    def search(self, term: str) -> None:
        """Search for modules by name or description"""
        term = term.lower()
        matching_modules = [
            module for module in self.modules.values()
            if term in module.name.lower() or term in module.description.lower()
        ]
        
        if not matching_modules:
            print(f"{Colors.WARNING}[!] No modules found matching: {term}{Colors.ENDC}")
            return
            
        print(f"\n{Colors.SUCCESS}[*] Results for '{term}':{Colors.ENDC}")
        self._display_modules_table(matching_modules)