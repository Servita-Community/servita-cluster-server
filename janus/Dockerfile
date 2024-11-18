# Use an official Ubuntu as a parent image
FROM ubuntu:20.04

# Set non-interactive mode for installation
ENV DEBIAN_FRONTEND=noninteractive

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    wget \
    cmake \
    meson \
    pkg-config \
    libtool \
    automake \
    libmicrohttpd-dev \
    libjansson-dev \
    libssl-dev \
    libsofia-sip-ua-dev \
    libconfig-dev \
    libglib2.0-dev \
    libopus-dev \
    libogg-dev \
    libcurl4-openssl-dev \
    liblua5.3-dev \
    build-essential \
    ca-certificates \
    vim

# Install libnice
RUN git clone https://gitlab.freedesktop.org/libnice/libnice /tmp/libnice && \
    cd /tmp/libnice && \
    meson --prefix=/usr build && ninja -C build && sudo ninja -C build install

# Install libsrtp
RUN apt-get remove -y --purge libsrtp2-dev libsrtp2-1 && \
    wget https://github.com/cisco/libsrtp/archive/v2.2.0.tar.gz && \
    tar xfv v2.2.0.tar.gz && cd libsrtp-2.2.0 && \
    ./configure --prefix=/usr --enable-openssl && \
    make shared_library && sudo make install

# Install usrsctp
RUN git clone https://github.com/sctplab/usrsctp /tmp/usrsctp && \
    cd /tmp/usrsctp && \
    ./bootstrap && \
    ./configure --prefix=/usr --disable-programs --disable-inet --disable-inet6 && \
    make && sudo make install

# Install libwebsockets
RUN git clone https://libwebsockets.org/repo/libwebsockets /tmp/libwebsockets && \
    cd /tmp/libwebsockets && \
    mkdir build && cd build && \
    cmake -DLWS_MAX_SMP=1 -DLWS_WITHOUT_EXTENSIONS=0 -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_C_FLAGS="-fpic" .. && \
    make && sudo make install

# Install Janus Gateway
RUN git clone https://github.com/meetecho/janus-gateway.git /tmp/janus-gateway && \
    cd /tmp/janus-gateway && \
    sh autogen.sh && \
    ./configure --disable-rabbitmq --disable-mqtt --enable-data-channels --enable-websockets --prefix=/opt/janus && \
    make && sudo make install && sudo make configs

# Configure Janus Gateway
COPY janus.plugin.streaming.jcfg.template /opt/janus/etc/janus/janus.plugin.streaming.jcfg
RUN sed -i -E 's/^(\s*)#?(full_trickle\s*=\s*).*/\1\2true/' /opt/janus/etc/janus/janus.jcfg

# Expose Janus Gateway ports (if needed)

RUN apt-get install -y tcpdump

# Set up the entry point to start Janus Gateway
ENTRYPOINT ["/opt/janus/bin/janus"]

EXPOSE 5000 5001
