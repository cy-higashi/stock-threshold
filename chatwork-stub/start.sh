#!/bin/sh
exec socat TCP-LISTEN:8080,reuseaddr,fork EXEC:/stub/stub.sh
