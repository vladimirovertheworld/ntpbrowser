#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Set Git user configuration
git config --global user.email "vladimir@overtheworld.uk"
git config --global user.name "vladimirovertheworld"

# Show current directory contents
echo "Current directory contents:"
ls -la

# Ask user for the directory to add to .gitignore
read -p "Enter the directory you want to add to .gitignore: " IGNORE_DIR

# Create .gitignore file if it doesn't exist and add the directory
echo "$IGNORE_DIR/" >> .gitignore

# Repository URL
REPO_URL="https://github.com/vladimirovertheworld/ntpbrowser.git"

# Initialize Git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: NTP Browser application"

# Add remote origin
git remote add origin $REPO_URL

# Push to GitHub
git push -u origin master

echo "Repository has been initialized and pushed to $REPO_URL"

# If you're using GitHub CLI, uncomment the following lines and comment out the git push command above
# gh repo create vladimirovertheworld/ntpbrowser --public --source=. --remote=origin
# git push -u origin master

echo "Script completed successfully!"
