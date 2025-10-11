#!/usr/bin/env python3
"""
F-Droid APK Fetcher and Metadata Generator

This script:
1. Reads apps.yml configuration
2. Fetches latest releases from GitHub repositories
3. Downloads APK files to repo/ directory
4. Generates F-Droid metadata files
"""

import os
import sys
import json
import yaml
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class APKFetcher:
    def __init__(self, config_file: str = "apps.yml"):
        self.config_file = config_file
        self.repo_dir = Path("repo")
        self.metadata_dir = Path("metadata")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        
        # Set up GitHub API authentication if token is available
        if self.github_token:
            self.session.headers.update({
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            })
        
        # Create directories if they don't exist
        self.repo_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> List[Dict]:
        """Load apps configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('apps', [])
        except FileNotFoundError:
            print(f"Error: Configuration file {self.config_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            sys.exit(1)
    
    def get_latest_release(self, repo: str) -> Optional[Dict]:
        """Fetch latest release information from GitHub API"""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️  No releases found for {repo}")
            else:
                print(f"⚠️  Error fetching release for {repo}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Network error for {repo}: {e}")
            return None
    
    def find_apk_asset(self, assets: List[Dict]) -> Optional[Dict]:
        """Find APK file in release assets"""
        for asset in assets:
            if asset['name'].endswith('.apk'):
                return asset
        return None
    
    def download_apk(self, asset: Dict, package_name: str) -> Optional[Path]:
        """Download APK file to repo directory"""
        apk_url = asset['browser_download_url']
        apk_name = asset['name']
        target_path = self.repo_dir / apk_name
        
        # Check if file already exists
        if target_path.exists():
            print(f"✓ APK already exists: {apk_name}")
            return target_path
        
        print(f"⬇️  Downloading {apk_name}...")
        
        try:
            response = self.session.get(apk_url, stream=True)
            response.raise_for_status()
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Downloaded: {apk_name}")
            return target_path
        except requests.exceptions.RequestException as e:
            print(f"✗ Error downloading APK: {e}")
            return None
    
    def generate_metadata(self, app_config: Dict, release: Dict) -> None:
        """Generate F-Droid metadata file for an app"""
        package_name = app_config['package_name']
        metadata_file = self.metadata_dir / f"{package_name}.yml"
        
        # Extract version info from release
        version_name = release['tag_name'].lstrip('v')
        published_date = release['published_at'].split('T')[0]
        
        metadata = {
            'Categories': app_config.get('categories', ['Utilities']),
            'License': app_config.get('license', 'Unknown'),
            'AuthorName': app_config.get('author', 'Unknown'),
            'AuthorWebSite': f"https://github.com/{app_config['github_repo']}",
            'SourceCode': f"https://github.com/{app_config['github_repo']}",
            'IssueTracker': f"https://github.com/{app_config['github_repo']}/issues",
            'Summary': app_config.get('summary', app_config['app_name']),
            'Description': app_config.get('description', app_config.get('summary', '')),
            'Name': app_config['app_name'],
            'AutoName': app_config['app_name'],
        }
        
        # Write metadata file
        with open(metadata_file, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        print(f"✓ Generated metadata: {metadata_file.name}")
    
    def process_app(self, app_config: Dict) -> bool:
        """Process a single app: fetch release and download APK"""
        repo = app_config['github_repo']
        package_name = app_config['package_name']
        
        print(f"\n📱 Processing {app_config['app_name']} ({repo})")
        
        # Get latest release
        release = self.get_latest_release(repo)
        if not release:
            return False
        
        # Find APK in assets
        assets = release.get('assets', [])
        apk_asset = self.find_apk_asset(assets)
        
        if not apk_asset:
            print(f"⚠️  No APK found in latest release")
            return False
        
        # Download APK
        apk_path = self.download_apk(apk_asset, package_name)
        if not apk_path:
            return False
        
        # Generate metadata
        self.generate_metadata(app_config, release)
        
        return True
    
    def run(self) -> int:
        """Main execution method"""
        print("🚀 F-Droid APK Fetcher Starting...")
        print("=" * 60)
        
        apps = self.load_config()
        
        if not apps:
            print("⚠️  No apps configured in apps.yml")
            return 1
        
        print(f"Found {len(apps)} app(s) to process")
        
        success_count = 0
        for app in apps:
            if self.process_app(app):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully processed {success_count}/{len(apps)} app(s)")
        
        return 0 if success_count > 0 else 1


if __name__ == "__main__":
    fetcher = APKFetcher()
    sys.exit(fetcher.run())

