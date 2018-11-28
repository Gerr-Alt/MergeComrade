# Merge Comrade
This Telegram bot was initially develop to manage queue to merge in the project main branch (to minimize conflicts in case if multiple persons want to merge).
See Notes.txt for the basic information of how to build and start container.

## Basic information
This is Telegram bot, written on Python 3.5. It can work in two modes, webhook or polling. Polling mode can be used to start bot from the developer machine, any server, etc, while Webhook requires server with HTTPS, A+ graded by https://www.ssllabs.com/ssltest/.

## Environment Variables
Next environment variables can be used to setup bot:
* TOKEN (required) - Telegram Bot API token, for more information see https://core.telegram.org/bots/api
* WORKING_DIR (required) - working dir, which should contain 'config.json' file and also will be used to store state
* ENV_VARIABLE_WEBHOOK_ENABLED - should be TRUE in case if Webhook is used
* ENV_VARIABLE_HOST - hostname, which will be used for Webhook (default 'localhost')
* ENV_VARIABLE_PORT - port, which will be used for Webhook (default 443)

## Docker
Bot was designed to be encapsulated in the Docker container. Docker file is located at the root of repository. In the polling mode bot can be started with the next command:
```
docker run -d -v /etc/bot:/etc/bot \
           -e "TOKEN=<Telegram Token>" \
           -e "WORKING_DIR=/etc/bot" \
           --restart on-failure \
           bot
```

More complex example, when Webhook is used:
```
docker run -d -v /etc/bot:/etc/bot \
           -e "TOKEN=<Telegram Token>" \
           -e "WORKING_DIR=/etc/bot" \
           -e "WEBHOOK=TRUE"
           -e "VIRTUAL_HOST=<Bot host if webhook is used, e.g example.com>" \
           --restart on-failure \
           bot
```

## How to get A+?
The simpliest way is to use LetsEncrypt + Nginx Reverse Proxy container.
Ensure, that you have started VM somewhere, registered domain, and correct setup of the DNS, which resolves this domain to IP of the VM.
After that, run the next command on the VM:
```
sudo docker run -it --rm -p 443:443 -p 80:80 --name certbot \
            -v "/etc/letsencrypt:/etc/letsencrypt" \
            -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
            quay.io/letsencrypt/letsencrypt:latest certonly
```
You will need to run temporary server, enter your domain domain (which should be resolved to the current VM), and, if everything is correct, you will get your certificates.
After that, you can copy them to the `/var/lib/certificates` folder in the next way:
* fullchain.pem as domain.name.crt
* privkey.pem as domain.name.key

After that, you can run container with Nginx Reverse Proxy with command `docker run -d -p 80:80 -p 443:443 -v /var/lib/certificates:/etc/nginx/certs -v /var/run/docker.sock:/tmp/docker.sock:ro jwilder/nginx-proxy`. This container will 'listen' to the any other containers with variable 'VIRTUAL_HOST', and, if one appears, it will automatically start to serve all the requests for this domain name to this container.
