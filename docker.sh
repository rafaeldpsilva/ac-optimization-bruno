docker buildx build --platform linux/arm64 -t rdpds/ac-optimization .
docker tag rdpds/ac-optimization rdpds/ac-optimization:latest
docker tag rdpds/ac-optimization rdpds/ac-optimization:v0.1.1
docker push --all-tags rdpds/ac-optimization