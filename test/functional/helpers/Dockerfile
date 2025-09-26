# Simple HTTPS server with custom CA certificates made with mkcert
FROM alpine:latest

RUN apk add --no-cache curl bash openssl && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then MKCERT_ARCH="linux/amd64"; else MKCERT_ARCH="linux/arm64"; fi && \
    curl -JLO "https://dl.filippo.io/mkcert/latest?for=${MKCERT_ARCH}" && \
    mv mkcert-v*-* /usr/local/bin/mkcert && \
    chmod +x /usr/local/bin/mkcert

WORKDIR /srv

EXPOSE 4433

CMD ["/bin/bash", "-c", "mkcert -install && mkcert simple-https-server && openssl s_server -cert simple-https-server.pem -key simple-https-server-key.pem -www"]
