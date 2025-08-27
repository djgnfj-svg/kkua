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
sudo systemctl stop nginx
sed -i 's/POSTGRES_PASSWORD=your-secure-db-password-here/POSTGRES_PASSWORD=your-secure-postgres-password-change-me/g' .env.prod
sed -i 's/DATABASE_URL=postgresql:\/\/postgres:your-secure-db-password-here@db:5432\/kkua_db/DATABASE_URL=postgresql:\/\/postgres:your-secure-postgres-password-change-me@db:5432\/kkua_db/g' .env.prod
sed -i 's/SECRET_KEY=your-super-secret-key-change-this-in-production/SECRET_KEY=1fc6a705376e263b9335760a33b8b5517dfc1349b32f5e19aa3569bca44380b0/g' .env.prod  
sed -i 's/JWT_SECRET=your-jwt-secret-key-change-this-in-production/JWT_SECRET=1d195f2f75c1f1417ce7adfe7b0b3838394fff27b88ee05a2fa8299daed8707c/g' .env.prod
```

```bash
bash prod.sh
```

**접속:** http://54.180.88.143:80