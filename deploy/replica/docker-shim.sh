#!/bin/bash
# Stand-in for the `docker` CLI INSIDE the replica. In production the deploy script runs on the host and calls
# `docker exec django_server ...`; in the replica the "host" and the "container" are the same machine, so this
# shim just runs the command locally. It supports exactly what deploy/acapp_deploy_server.py and install_server.py use:
#   docker ps ...                         -> prints django_server
#   docker exec [-i] [-u USER] C cmd...   -> runs cmd (as USER) here
#   docker cp C:SRC DEST                  -> cp SRC DEST
sub="$1"; shift
case "$sub" in
  ps)
    echo django_server ;;
  exec)
    user=""
    while [ $# -gt 0 ]; do
      case "$1" in
        -i|-t|-it) shift ;;
        -u) user="$2"; shift 2 ;;
        *) break ;;
      esac
    done
    shift   # the container name
    if [ -n "$user" ]; then exec runuser -u "$user" -- "$@"; else exec "$@"; fi ;;
  cp)
    cp "${1#*:}" "$2" ;;
  *)
    echo "docker shim: unsupported command: $sub" >&2; exit 1 ;;
esac
