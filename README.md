一个简单得2FA 动态密钥生成器
 根据用户名匹配对应的密钥 然后前端获取2FA的动态验证码


Docker 部署
可以直接拉取镜像


```
docker pull miku7117/flask-2fa:latest
```

```
docker run -d -p 5000:5000 --name flask-2fa miku7117/flask-2fa:latest
```

反代使用 
Nginx Proxy Manager


也可以使用
docker-compose.yml
```
version: "3.9"

services:
  2fa-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flask-2fa
    ports:
      - "5000:5000"  # 将容器的 5000 端口绑定到主机
    volumes:
      - ./2fa.db:/app/2fa.db  # 数据库持久化
      - ./templates:/app/templates  # 模板文件挂载
      - ./static:/app/static        # 静态文件挂载
    environment:
      - FLASK_ENV=development  # Flask 环境变量
    restart: always  # 容器崩溃时自动重启
```
