FROM python:3.12-alpine as builder

WORKDIR /build

# install ffmpeg:
RUN apk add ffmpeg

# install pdm:
RUN pip install pdm==2.15.4

# copy shared libs:
COPY lib/podcastie_configs lib/podcastie_configs
COPY lib/podcastie_database lib/podcastie_database
COPY lib/podcastie_rss lib/podcastie_rss

# copy notifier service pdm files
COPY services/notifier/pyproject.toml services/notifier/pdm.lock* services/notifier/

# install dependencies and the project:
RUN cd services/notifier/ && mkdir __pypackages__ && pdm install --prod --no-lock --no-editable


FROM python:3.12 as runner

WORKDIR /app

# copy dependencies
COPY --from=builder /build/services/notifier/__pypackages__/ __pypackages__/
COPY --from=builder /usr/bin/ffmpeg /usr/bin/ffmpeg

# copy notifier package
COPY services/notifier/notifier notifier

ENV PYTHONPATH=/app/__pypackages__/3.12/lib
ENTRYPOINT ["python", "-m", "notifier"]
