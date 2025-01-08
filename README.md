一个简单得2FA 动态密钥生成器
 根据用户名匹配对应的密钥 然后前端获取2FA的动态验证码


Docker 部署


```
docker pull miku7117/flask-2fa:latest
```

```
docker run -d -p 5000:5000 --name flask-2fa miku7117/flask-2fa:latest
```

反代使用 
Nginx Proxy Manager
