import os
import json
import urllib.request
import urllib.error
import concurrent.futures

def fetch_repo(repo, url_mapping):
    if repo == "username/repo-name":
        return

    print(f"Checking {repo}...")
    try:
        # Use GitHub API to get latest release
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Python-urllib'}
        
        # Check for GITHUB_TOKEN environment variable
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"Rate limit exceeded or forbidden for {repo}")
            else:
                print(f"Failed to get release for {repo}: {e.code}")
            return
            
        tag_name = data.get('tag_name')
        assets = data.get('assets', [])
        
        for asset in assets:
            name = asset['name']
            if name.endswith('.apk'):
                download_url = asset['browser_download_url']
                target_path = os.path.join('repo', name)
                
                # Save mapping (thread-safe enough for dict assignment in CPython, but let's be careful if we expand)
                url_mapping[name] = download_url

                if os.path.exists(target_path):
                    print(f"  Skipping {name} (already exists)")
                    continue
                    
                print(f"  Downloading {name}...")
                try:
                    with urllib.request.urlopen(download_url) as r, open(target_path, 'wb') as f:
                        while True:
                            chunk = r.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                    print(f"  Downloaded {name}")
                except Exception as e:
                    print(f"  Failed to download {name}: {e}")
                    
    except Exception as e:
        print(f"Error processing {repo}: {e}")

def fetch_apks():
    try:
        with open('repos.json', 'r') as f:
            repos = json.load(f)
    except FileNotFoundError:
        print("repos.json not found.")
        return

    if not os.path.exists('repo'):
        os.makedirs('repo')

    url_mapping = {}
    
    # Use ThreadPoolExecutor to fetch repos in parallel
    # Adjust max_workers as needed, 5 is usually a safe number for network I/O
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_repo, repo, url_mapping) for repo in repos]
        concurrent.futures.wait(futures)

    # Save URL mapping
    with open('url_mapping.json', 'w') as f:
        json.dump(url_mapping, f, indent=2)
    print("Saved url_mapping.json")

if __name__ == "__main__":
    fetch_apks()
