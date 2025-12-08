#!/bin/bash
set -e

echo "[$(date)] Starting F-Droid update check..."

# Change to data directory
cd /data

# Copy config files if not present
if [ ! -f config.yml ]; then
    cp /app/config.yml .
fi

# Read repos from repos.json
REPOS=$(cat /app/repos.json | python3 -c "import sys, json; print(' '.join(json.load(sys.stdin)))")

# Create repo directory if it doesn't exist
mkdir -p repo

# Track if any APKs were downloaded
DOWNLOADED=0

# Fetch APKs from GitHub releases
for REPO in $REPOS; do
    echo "Checking $REPO..."
    
    # Get latest release info
    RELEASE_JSON=$(curl -s "https://api.github.com/repos/$REPO/releases/latest")
    
    # Extract APK URLs
    APK_URLS=$(echo "$RELEASE_JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    assets = data.get('assets', [])
    for asset in assets:
        if asset['name'].endswith('.apk'):
            print(asset['browser_download_url'])
except:
    pass
")
    
    # Download each APK
    for URL in $APK_URLS; do
        FILENAME=$(basename "$URL")
        
        # Check if file already exists
        if [ -f "repo/$FILENAME" ]; then
            echo "  $FILENAME already exists, skipping"
            continue
        fi
        
        echo "  Downloading $FILENAME..."
        curl -L -o "repo/$FILENAME" "$URL"
        DOWNLOADED=1
    done
done

# Only run fdroid update if new APKs were downloaded
if [ $DOWNLOADED -eq 1 ]; then
    echo "New APKs found, updating F-Droid index..."
    
    # Configure keystore in config.yml
    cat >> config.yml << EOF
keystore: /app/keystore.jks
repo_keyalias: ${FDROID_KEY_ALIAS}
keystorepass: ${FDROID_KEYSTORE_PASS}
keypass: ${FDROID_KEY_PASS}
EOF
    
    # Run fdroid update
    fdroid update --create-metadata --pretty
    
    # Sign the index
    fdroid signindex
    
    # Remove keystore config from config.yml
    head -n 5 config.yml > config.yml.tmp
    mv config.yml.tmp config.yml
    
    echo "F-Droid index updated successfully!"
else
    echo "No new APKs found."
fi

echo "[$(date)] Update check complete."
