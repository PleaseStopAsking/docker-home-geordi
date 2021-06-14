## Get list of file extensions
```find /example/path -type f | sed 's|.*\.||' | sort -u```

## Get list of files that match a given syntax
```find /example/path -name "*.txt" -print```


## Delete list of files that match a given syntax
```find /example/path -name "*.txt" -delete```


## Change file extension to lowercase for a given type
```find /example/path -type f -name "*.MP4" -exec rename 's/\.MP4$/.mp4/' '{}' \;```


## Run plex-meta-manager one time
```docker run --rm -it -v /root/docker-home-geordi/docker-configs/plex-meta-manager:/config:rw meisnate12/plex-meta-manager --config /config/config.yml --run```


## Move data from one disk to another
This is used when a small disk is getting replaced with a larger disk and you have the ability to copy data from the small drive to another existing drive before pulling the small drive. This is dependant on another drive having the free space to handle the small drives data.

Details:
    Merging 2 folders together:

    rsync -abviuP src/ dest/

        -a, --archive               archive mode; equals -rlptgoD (no -H,-A,-X)
        -b, --backup                make backups (see --suffix & --backup-dir)
        -v, --verbose               increase verbosity
        -i, --itemize-changes       output a change-summary for all updates
        -u, --update                skip files that are newer on the receiver
        -P                          same as --partial --progress


Working Example:  
```rsync -abviuP /srv/dev-disk-by-label-data3/data/media/Movies/ /srv/dev-disk-by-label-data5/data/media/Movies/```

Once the data has been copied to the new drive, run `snapraid diff` to confirm the data is marked as `Copied` and if correct, run `snapraid sync` to finalize the copy. With the data now moved and syncd, you an delete the data from the original drive and run `snapraid sync` one last time to finalize the process.

## Re-balance data from a single disk into the drive pool
This process is simliar to the above workflow except the destintation in the rsync points to the drive pool and not a single drive.

```rsync -abviuP srv/dev-disk-by-label-data3/data/media/Movies/ /srv/8d19a07a-03d5-45f1-85dc-ccd49430f386/data/media/Movies/```

## Removing a disk from SnapRAID array
This process must be done at both the OpenMediaVault GUI level as well as the CLI

1. Create an empty directory  

    ```mkdir /tmp/empty/```

2. Edit the SnapRAID config file manually to change the path to the disk you wish to remove from the array  
    
    ```sudo nano /etc/snapraid.conf```

    Original
    ```
        #####################################################################
        # OMV-Name: data2  Drive Label: data2
        content /srv/dev-disk-by-label-data2/snapraid.content
        disk data2 /srv/dev-disk-by-label-data2
    ```
    Modified
    ```
    #####################################################################
        # OMV-Name: data2  Drive Label: data2
        disk data2 /tmp/empty/
    ```

3. Execute a SnapRAID sync with force empty mode to ignore missing disk  
    
    ```snapraid sync -E```

4. From the OMV GUI, completely remove the disk from the `SnapRAID` plugin panel  

5. From the OMV GUI, completely remove the disk from the `Union Filesystems` plugin panel    
    - This will require a restart of the system to finalize   

6. Unmount the disk from the `File Systems` panel

7. Wipe the disk from the `Disks` panel

## Troubleshoot container DNS/Network issues
```docker run --rm -it ubuntu bash -c "apt update && apt install curl -y && curl ipecho.net/plain"```

```docker run --rm -it alpine sh -c "apk add curl && curl ipecho.net/plain"```

```docker run --rm -it alpine sh -c "apk add curl && curl https://api.ipify.org?format=json"```

```docker run busybox ping -c 1 192.203.230.10```

```docker run busybox nslookup google.com```

## Traefik label example for authelia auth
    - traefik.enable=true
    - traefik.http.services.transmission.loadbalancer.server.port=9091
    - traefik.http.routers.transmission.rule=Host(`transmission.${traefik_duckdns_domain}`)
    - traefik.http.routers.transmission.entrypoints=https
    - traefik.http.routers.transmission.tls=true
    - traefik.http.routers.transmission.tls.certresolver=letsencrypt
    - traefik.http.routers.transmission.middlewares=authelia@docker,baseline-secureheaders@file,baseline-ratelimits@file

## Authelia compose example
  authelia:
    container_name: authelia
    environment:
      - TZ=${timezone}
    expose:
      - 7443
    healthcheck:
      disable: true
    hostname: authelia
    image: authelia/authelia:4.29.4
    labels:
      - traefik.enable=true
      - traefik.http.routers.authelia.rule=Host(`login.${traefik_duckdns_domain}`)
      - traefik.http.routers.authelia.entrypoints=https
      - traefik.http.routers.authelia.tls=true
      - traefik.http.routers.authelia.tls.certresolver=letsencrypt
      - traefik.http.middlewares.authelia.forwardauth.address=http://authelia:7443/api/verify?rd=https://login.${traefik_duckdns_domain}
      - traefik.http.middlewares.authelia.forwardauth.trustForwardHeader=true
      - traefik.http.middlewares.authelia.forwardauth.authResponseHeaders=X-Forward-User
    restart: unless-stopped
    volumes:
      - authelia:/config
      - ./docker-configs/authelia/configuration.yml:/config/configuration.yml:ro
      - ./docker-configs/authelia/users_database.yml:/config/users_database.yml:ro