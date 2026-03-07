group "default" {
  targets = ["musicmetacleaner"]
}

target "musicmetacleaner" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["musicmetacleaner:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}
