docker run \
        --name openhab \
        --net=host \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/timezone:/etc/timezone:ro \
        -v /opt/openhab/conf:/openhab/conf \
        -v /opt/openhab/userdata:/openhab/userdata \
        -v /opt/openhab/addons:/openhab/addons \
        -d \
        -e USER_ID=1001 \
        -e GROUP_ID=9001 \
        -e CRYPTO_POLICY=unlimited \
        --restart=always \
	openhab/openhab:3.4.4
