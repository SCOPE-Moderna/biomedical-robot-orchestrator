# Compile protos, nodes
FROM node:lts-alpine3.20 AS build

COPY nodes /nodes
COPY protos /protos

WORKDIR /nodes
RUN apk add protobuf-dev
RUN yarn
RUN yarn protos
RUN yarn compile

WORKDIR /nodes/dist
RUN yarn

# Run Node-RED
FROM nodered/node-red

# Copy in compiled nodes
COPY --from=build /nodes/dist /nodes-out

# Add custom nodes
WORKDIR /usr/src/node-red
RUN npm install /nodes-out --unsafe-perm --no-update-notifier --no-fund --only=production

