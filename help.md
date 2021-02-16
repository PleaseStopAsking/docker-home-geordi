# Get list of file extensions
find /example/path -type f | sed 's|.*\.||' | sort -u

# Get list of files that match a given syntax
find /example/path -name "*.txt" -print

# Delete list of files that match a given syntax
find /example/path -name "*.txt" -delete

# Run plex-auto-collections for movies
docker run --rm -v /root/docker-home-geordi/docker-configs/plex-auto-collections:/config:rw mza921/plex-auto-collections -c /config/config-movie.yml --update

# Run plex-auto-collections for tv
docker run --rm -v /root/docker-home-geordi/docker-configs/plex-auto-collections:/config:rw mza921/plex-auto-collections -c /config/config-tv.yml --update