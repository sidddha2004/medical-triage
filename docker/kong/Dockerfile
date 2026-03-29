FROM kong:3-alpine

# Copy declarative configuration
COPY kong.yml /kong/kong.yml

# Set environment variables
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/kong/kong.yml
ENV KONG_DNS_ORDER=LAST,A,CNAME
ENV KONG_PLUGINS=bundled

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD kong health || exit 1

EXPOSE 8000 8443 8001 8444
