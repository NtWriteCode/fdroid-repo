FROM python:3.14-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    cron \
    && pip install --no-cache-dir fdroidserver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy scripts
COPY scripts/poll_and_update.sh /app/poll_and_update.sh
RUN chmod +x /app/poll_and_update.sh

# Create cron job
RUN echo "*/15 * * * * cd /app && /app/poll_and_update.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/fdroid-poll
RUN chmod 0644 /etc/cron.d/fdroid-poll
RUN crontab /etc/cron.d/fdroid-poll
RUN touch /var/log/cron.log

# Start cron and tail logs
CMD cron && tail -f /var/log/cron.log
