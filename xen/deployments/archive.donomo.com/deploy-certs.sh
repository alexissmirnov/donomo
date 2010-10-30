#!/bin/bash

wrk_dir="$(cd $(dirname "$0") && pwd)"

echo "Installing private key"
openssl rsa \
    -in  "$wrk_dir/archive.donomo.com.key" \
    -out "/etc/ssl/private/donomo.key"

echo "Installing certificate chain"
cat "$wrk_dir/archive.donomo.com.crt" "$wrk_dir/gd_bundle.crt" \
    > "/etc/ssl/certs/donomo.crt"

echo "Done."