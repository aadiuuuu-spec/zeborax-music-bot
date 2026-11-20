FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/zeborax ./cmd/bot

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=build /out/zeborax /app/zeborax
ENV PORT=8080
EXPOSE 8080
USER 10001:10001
ENTRYPOINT ["/app/zeborax"]
