# Get list of file extensions
find /example/path -type f | sed 's|.*\.||' | sort -u

# Get list of files that match a given syntax
find /example/path -name "*.txt" -print

# Delete list of files that match a given syntax
find /example/path -name "*.txt" -delete