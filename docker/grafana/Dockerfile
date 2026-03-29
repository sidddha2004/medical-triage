FROM grafana/grafana:10.2.0

USER root
RUN apk add --no-cache curl

USER grafana

# Copy provisioning
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /etc/grafana/provisioning/dashboards/

# Environment variables
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false

EXPOSE 3000
