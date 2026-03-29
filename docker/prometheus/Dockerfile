FROM prom/prometheus:v2.48.0

# Copy configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alerts.yml /etc/prometheus/alerts.yml

# Create data directory
RUN mkdir -p /prometheus/data && \
    chown -R nobody:nobody /prometheus/data

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -q -O /dev/null http://localhost:9090/-/healthy || exit 1

EXPOSE 9090
