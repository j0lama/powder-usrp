#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "USE: $0 <GitHub Token> <Dockerhub User> <Dockerhub Password>"
    exit 1
fi

# Install docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
# Add the repository to Apt sources:
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt install -y docker-ce
sudo usermod -aG docker $USER
newgrp docker

# Clone cell-scanner-docker
git clone https://j0lama:$1@github.com/j0lama/cell-scanner-docker.git

# Clone ng-scope-docker
git clone https://j0lama:$1@github.com/j0lama/ng-scope-docker.git

echo "$3" | docker login -u "$2" --password-stdin