FROM eclipse-temurin:17-jdk-jammy
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-tk xvfb openbox xdotool xauth \
    libgl1-mesa-dri libgl1 libglu1-mesa libxrandr2 libxcursor1 libxi6 \
    libxinerama1 libxxf86vm1 libasound2 libopenal1 ffmpeg \
    git ripgrep curl unzip ca-certificates build-essential cmake \
    libpng-dev libjpeg-dev libfreetype6-dev libsqlite3-dev libzstd-dev \
    zlib1g-dev libgmp-dev libjsoncpp-dev libcurl4-openssl-dev libluajit-5.1-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir PyAutoGUI==0.9.54 mss==10.1.0 Pillow==11.3.0
RUN useradd --create-home --uid 1000 worker && mkdir /workspace && chown worker /workspace
COPY worker.py /opt/repro/worker.py
COPY entrypoint.sh /opt/repro/entrypoint.sh
RUN chmod +x /opt/repro/entrypoint.sh
USER worker
ENV DISPLAY=:99 XAUTHORITY=/home/worker/.Xauthority LIBGL_ALWAYS_SOFTWARE=1 ALSOFT_DRIVERS=null
WORKDIR /workspace/repo
ENTRYPOINT ["/opt/repro/entrypoint.sh"]
