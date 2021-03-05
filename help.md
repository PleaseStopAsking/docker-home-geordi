# Get list of file extensions
find /example/path -type f | sed 's|.*\.||' | sort -u

# Get list of files that match a given syntax
find /example/path -name "*.txt" -print

# Delete list of files that match a given syntax
find /example/path -name "*.txt" -delete

# Change file extension to lowercase for a given type
find /example/path -type f -name "*.MP4" -exec rename 's/\.MP4$/.mp4/' '{}' \;

# Run plex-meta-manager one time
docker run --rm -it -v /root/docker-home-geordi/docker-configs/plex-meta-manager:/config:rw meisnate12/plex-meta-manager --config /config/config.yml --run