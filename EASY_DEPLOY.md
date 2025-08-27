# KKUA 프로덕션 배포

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER && newgrp docker
```

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
```

```bash
rm -rf kkua && git clone https://github.com/djgnfj-svg/kkua.git && cd kkua && chmod +x *.sh
```

```bash
docker system prune -af && bash prod.sh
```

**접속:** http://43.200.171.149