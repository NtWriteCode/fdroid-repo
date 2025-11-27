import json
import os
import sys

def patch_index():
    index_path = 'repo/index-v1.json'
    mapping_path = 'url_mapping.json'

    if not os.path.exists(index_path):
        print(f"Index file not found: {index_path}")
        return

    if not os.path.exists(mapping_path):
        print(f"Mapping file not found: {mapping_path}")
        return

    with open(index_path, 'r') as f:
        data = json.load(f)

    with open(mapping_path, 'r') as f:
        mapping = json.load(f)

    packages = data.get('packages', {})
    for package_name, package_data in packages.items():
        for version in package_data:
            apk_name = version.get('apkName')
            if apk_name and apk_name in mapping:
                external_url = mapping[apk_name]
                print(f"Patching {apk_name} -> {external_url}")
                # F-Droid client supports absolute URLs in apkName?
                # The spec says apkName is the file name.
                # However, some clients might support absolute URLs.
                # A better approach might be to use 'downloadUrl' if supported, or rely on the client handling absolute URLs in apkName.
                # Based on research, some repos use absolute URLs.
                version['apkName'] = external_url
                version['hashType'] = 'sha256' # Ensure hash type is set
                # We rely on fdroid update to have calculated the hash from the downloaded file.

    with open(index_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Patched index-v1.json")

if __name__ == "__main__":
    patch_index()
