FROM python:3.13-slim

WORKDIR /app

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends ffmpeg curl unzip fonts-noto-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

RUN deno --version

RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml uv.lock ./

# Refresh yt-dlp and its EJS challenge-solver dependency at image build time.
RUN uv lock --upgrade-package yt-dlp --upgrade-package yt-dlp-ejs \
    && uv sync --locked

COPY . .

CMD ["bash", "start"]
