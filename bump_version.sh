#!/bin/bash
# bump_version.sh
# Usage: ./bump_version.sh [major|minor|patch]

set -e

if [ ! -f VERSION ]; then
  echo "0.1.0" > VERSION
fi

version=$(cat VERSION)
IFS='.' read -r major minor patch <<< "$version"

case "$1" in
  major)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
  minor)
    minor=$((minor + 1))
    patch=0
    ;;
  patch|*)
    patch=$((patch + 1))
    ;;
esac

new_version="$major.$minor.$patch"
echo "$new_version" > VERSION
echo "Bumped version to $new_version" 