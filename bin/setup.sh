#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "USE: $0 <GitHub Token> <Dockerhub User> <Dockerhub Password>"
    exit 1
fi

# Install docker
sudo apt-get update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt install -y docker-ce

cd /local/repository/

# Clone cell-scanner-docker
git clone https://j0lama:$1@github.com/j0lama/cell-scanner-docker.git

# Clone ng-scope-docker
git clone https://j0lama:$1@github.com/j0lama/ng-scope-docker-cosmos.git

echo "$3" | sudo docker login -u "$2" --password-stdin