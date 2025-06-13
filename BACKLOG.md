These are backlog topis. 
IMPORTANT: They should not be implemented yet. 

* find a way to make the ALLOWED_HOSTS configurable via environment variables. 
* the tls config is hardcoded:

$ The file  traefik/dynamic/tls-config.yaml has hardcoded domain name for the letsencrypt certificate. This is not good since the end user will want to use a different base domain. We should use an environment varialbe such as "DOMAIN"
and regenerate this file when the stack is installed or updated. 
tls:
  certificates:
    - certFile: /etc/certs/live/vfservices.viloforge.com/fullchain.pem
      keyFile: /etc/certs/live/vfservices.viloforge.com/privkey.pem

* The app users have hardcoded database. This should be fixed.

* The databases management scripts all have hardcoded db names. We should parse the docker-compose.yml to find the database names. 
