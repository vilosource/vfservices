* find a way to make the ALLOWED_HOSTS configurable via environment variables. 
* the tls config is hardcoded:

$ The file  traefik/dynamic/tls-config.yaml has hardcoded domain name for the letsencrypt certificate. This is not good since the end user will want to use a different base domain. We should use an environment varialbe such as "DOMAIN"
and regenerate this file when the stack is installed or updated. 
tls:
  certificates:
    - certFile: /etc/certs/live/vfservices.viloforge.com/fullchain.pem
      keyFile: /etc/certs/live/vfservices.viloforge.com/privkey.pem

