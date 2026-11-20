FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/zeborax ./cmd/bot

FROM alpine:3.22
RUN apk add --no-cache ca-certificates ffmpeg
WORKDIR /app
COPY --from=build /out/zeborax /app/zeborax
RUN mkdir -p /app/data && chown -R 10001:10001 /app
ENV PORT=8080
ENV QUEUE_STATE_FILE=/app/data/queues.json
EXPOSE 8080
USER 10001:10001
ENTRYPOINT ["/app/zeborax"]
