import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style
from pentest.utils import get_scan_directory

PLUGIN_NAME = "Scrape"
PLUGIN_DESCRIPTION = "Scrape downloads resources (e.g., images, PHP files, HTML) from a website."
REQUIRED_TOOLS = ["requests", "beautifulsoup4", "colorama"]
PLUGIN_COMMANDS = {
    "Download Images (Recommended)": "images",
    "Download PHP Files": "php",
    "Download HTML Files": "html",
    "Custom Download": "custom"
}

def run(target, command):
    """
    Scrape the given target website for resources based on the selected file type.
    """
    def download_resource(url, output_dir):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or "unknown_resource"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"{Fore.GREEN}Resource saved: {filepath}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error while downloading {url}: {str(e)}{Style.RESET_ALL}")

    def process_site(site, tag, attr, extensions, file_type):
        base_dir = get_scan_directory(site)
        output_dir = os.path.join(base_dir, file_type)
        os.makedirs(output_dir, exist_ok=True)
        print(f"{Fore.YELLOW}\nAnalyzing the site: {site}{Style.RESET_ALL}")
        try:
            response = requests.get(site, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.find_all(tag)
            if not elements:
                print(f"{Fore.RED}No <{tag}> elements found on {site}{Style.RESET_ALL}")
                return
            found = False
            for elem in elements:
                url_attr = elem.get(attr)
                if url_attr:
                    resource_url = urljoin(site, url_attr)
                    for ext in extensions:
                        if resource_url.lower().split('?')[0].endswith(ext.lower()):
                            found = True
                            download_resource(resource_url, output_dir)
                            break
            if not found:
                print(f"{Fore.YELLOW}No resource with extensions {extensions} found on {site}{Style.RESET_ALL}")
        except requests.RequestException as e:
            print(f"{Fore.RED}Error processing {site}: {str(e)}{Style.RESET_ALL}")

    if command == "images":
        file_type = "images"
        extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
        tag = "img"
        attr = "src"
    elif command == "php":
        file_type = "php"
        extensions = (".php",)
        tag = "a"
        attr = "href"
    elif command == "html":
        file_type = "html"
        extensions = (".html", ".htm")
        tag = "a"
        attr = "href"
    elif command == "custom":
        ext_input = input("Enter extensions separated by commas (e.g., .js,.css): ").strip()
        if not ext_input:
            return f"{Fore.RED}No extension provided. Exiting.{Style.RESET_ALL}"
        extensions = tuple(ext.strip() for ext in ext_input.split(",") if ext.strip())
        file_type = input("Enter the folder name to save results (e.g., js, css): ").strip()
        if not file_type:
            return f"{Fore.RED}No folder name provided. Exiting.{Style.RESET_ALL}"
        tag = "a"
        attr = "href"
    else:
        return f"{Fore.RED}Invalid command for Scrape plugin.{Style.RESET_ALL}"

    process_site(target, tag, attr, extensions, file_type)
