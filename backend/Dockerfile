FROM python:3.13 AS build

# Install Boost
WORKDIR /boost
RUN wget https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz
RUN tar -xzvf boost_1_86_0.tar.gz
WORKDIR /boost/boost_1_86_0
RUN ./bootstrap.sh --prefix=/usr/local
RUN ./b2 install --with-system --with-thread --with-program_options

# Install requirements for building ur_rtde wheel
RUN apt-get update && apt-get clean && apt-get install -y build-essential protobuf-compiler
RUN apt-get install -y software-properties-common build-essential cmake

# Copy in code, install Python packages, make protos
COPY backend /backend
COPY protos /protos
WORKDIR /backend
RUN pip install --no-cache-dir -r /backend/requirements.txt
RUN make protos

# Fresh container to run protos
FROM python:3.13

# Copy in Python packages
COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
# Copy in Boost
COPY --from=build /usr/local/include/boost /usr/local/include/boost
COPY --from=build /usr/local /usr/local
# Copy in code
COPY --from=build /backend /backend
EXPOSE 50051

WORKDIR /
ENTRYPOINT ["python", "-m", "backend.main"]