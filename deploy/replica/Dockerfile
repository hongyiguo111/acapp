# A local stand-in for the production container AND host, used to test deploy/acapp_deploy_server.py end to end.
# Same OS and Python as production (Ubuntu 20.04, Python 3.8.10), same pinned packages, nginx + redis + tmux,
# uwsgi and daphne started by hand inside tmux panes (see start.sh), app in /home/acs/acapp.
# It also runs sshd and has a `docker` shim so the real installer / forced-command deploy can be rehearsed against it.
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev gcc libc6-dev tmux redis-server nginx openssl curl procps ca-certificates \
        libjpeg-dev zlib1g-dev openssh-server \
    && rm -rf /var/lib/apt/lists/*

# versions as running in production (pip3 list of the acs user)
RUN pip3 install --no-cache-dir \
        Django==3.2.8 channels==3.0.4 daphne==3.0.2 channels-redis==4.2.1 django-redis==5.4.0 redis==6.1.1 \
        thrift==0.22.0 pillow==10.4.0 requests==2.22.0 uWSGI==2.0.20

RUN useradd -m -u 1000 -s /bin/bash acs \
    && mkdir -p /home/acs/media /etc/nginx/cert \
    && openssl req -x509 -nodes -newkey rsa:2048 -days 3650 -subj "/CN=app7562.acapp.acwing.com.cn" \
        -keyout /etc/nginx/cert/acapp.key -out /etc/nginx/cert/acapp.pem \
    && rm -f /etc/nginx/sites-enabled/default \
    && chown -R acs:acs /home/acs

# sshd with a root password: ONLY for rehearsing install_server.py against this throw-away local image
COPY sshd_extra.conf /tmp/sshd_extra.conf
RUN mkdir -p /run/sshd && ssh-keygen -A && echo 'root:replica-pw' | chpasswd && cat /tmp/sshd_extra.conf >> /etc/ssh/sshd_config
COPY docker-shim.sh /usr/local/bin/docker
RUN chmod +x /usr/local/bin/docker

COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /usr/local/bin/start-services.sh
RUN chmod +x /usr/local/bin/start-services.sh

# PID 1 only keeps the container alive; setup_replica.py copies the app in and then runs start-services.sh
CMD ["tail", "-f", "/dev/null"]
