FROM debian:bookworm-slim as builder

WORKDIR /opt

ENV RYE_HOME="/opt/rye"
ENV PATH="$RYE_HOME/shims:$PATH"

# hadolint ignore=DL3008
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libssl-dev \
        liblzma-dev \
        libtirpc-dev \
        libevent-dev \
        libffi-dev \
        libxml2-dev \
        libopenblas-dev \
        libblas-dev \
        liblapack-dev \
        perl-base \
        libgl1


SHELL [ "/bin/bash", "-o", "pipefail", "-c" ]

# Install tinytex https://yihui.org/tinytex/#installation
# RUN curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh

RUN curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash && \
    rye config --set-bool behavior.global-python=true && \
    rye config --set-bool behavior.use-uv=true

COPY ./.python-version ./pyproject.toml ./requirements* ./README.md ./
# RUN rye pin "$(cat .python-version)" && \
#     rye sync


FROM mcr.microsoft.com/vscode/devcontainers/base:bookworm
COPY --from=builder /opt/rye /opt/rye

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gfortran \
        libblas-dev \
        liblapack-dev \
        libgl1

ENV RYE_HOME="/opt/rye"
ENV PATH="$RYE_HOME/shims:$PATH"
ENV PYTHONUNBUFFERED True

RUN rye config --set-bool behavior.global-python=true && \
    rye config --set-bool behavior.use-uv=true

RUN chown -R vscode $RYE_HOME
