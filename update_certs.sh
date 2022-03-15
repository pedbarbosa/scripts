#!/usr/bin/env bash

if [[ -z "${DOMAIN}" ]]; then
    echo "Variable 'DOMAIN' isn't set, quiting ..."
    exit 1
fi

# echo "Checking local certificate expiration date ..."
SWAG_EXPIRY=$(openssl x509 -enddate -noout -in ~/git/server-stack/swag/etc/letsencrypt/live/$DOMAIN/cert.pem)
PROXY_EXPIRY=$(openssl x509 -enddate -noout -in ~/git/server-stack/proxy/certs/cert.pem)

# echo "Checking remote certificate expiration date ..."
ROUTER_EXPIRY=$(openssl s_client -showcerts -servername router.$DOMAIN -connect router.$DOMAIN:443 2>/dev/null |  openssl x509 -inform pem -noout -enddate)

if ! [[ $SWAG_EXPIRY == $ROUTER_EXPIRY ]]; then
    echo "Certificate has been updated or dates do not match: ${ROUTER_EXPIRY}"
    scp ~/git/server-stack/swag/etc/letsencrypt/live/$DOMAIN/*.pem router:/etc/config/certs/ && ssh router '/etc/init.d/uhttpd restart'
fi

if ! [[ $SWAG_EXPIRY == $PROXY_EXPIRY ]]; then
    echo "Certificate has been updated or dates do not match: ${PROXY_EXPIRY}"
    cp ~/git/server-stack/swag/etc/letsencrypt/live/$DOMAIN/*.pem ~/git/server-stack/proxy/certs/ && docker restart proxy
fi

