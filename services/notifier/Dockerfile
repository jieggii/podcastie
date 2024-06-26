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
COPY lib/podcastie_telegram_html lib/podcastie_telegram_html

# copy notifier service pdm files
COPY services/notifier/pyproject.toml services/notifier/pdm.lock* services/notifier/

# install dependencies and the project:
RUN cd services/notifier/ && mkdir __pypackages__ && pdm install --prod --no-lock --no-editable --no-self


FROM python:3.12-alpine as runner

WORKDIR /app

# copy Python dependencies:
COPY --from=builder /build/services/notifier/__pypackages__/ __pypackages__/

# copy binary dependenies (ffmpeg and ffprobe):
COPY --from=builder /usr/bin/ffmpeg /usr/bin/ffmpeg
COPY --from=builder /usr/bin/ffprobe /usr/bin/ffprobe

# copy shared libraries needed for the binary dependencies:
# > NOTE: I could have copied only selected libs, but ffprobe requires
# > dozens of them, so it is simpler just to copy the whole /usr/lib.
COPY --from=builder /usr/lib/ /usr/lib/

# copy notifier Python package:
COPY services/notifier/notifier notifier

ENV PYTHONPATH=/app/__pypackages__/3.12/lib
ENTRYPOINT ["python", "-m", "notifier"]
