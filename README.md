## Installation

## New Setup

Clone IEE Backend

```
git clone https://github.com/daran6255/IEE_Backend.git
cd IEE_Backend
nano .env
```

Add the following to `.env` file

```
ENV='prod/dev'
PLATFORM='win/linux'
SECRET_KEY='some-key'
HOST='http://127.0.0.1:3000'
UPLOAD_DIR='uploads'

# smtp variables
EMAIL_DOMAIN='smtp.<domaon>.com'
EMAIL_ADDRESS='admin.iee@winvinaya.com'
EMAIL_PASSWORD='<your-password>'

# DB variables
DB_HOST = 'localhost'
DB_USER = 'winvinaya_iee'
DB_PASSWORD = 'password'
DB_NAME = 'invoice_extraction'
DB_PORT = 3306

# Invoice variables
CREDITS_VALUE = 2
CREDITS_PER_PAGE = 5

# AWS Credentials - Keep the same key name
AWS_ACCESS_KEY_ID='ABCDEF123456'
AWS_SECRET_ACCESS_KEY='fas5446DSF456Ffds456'
AWS_DEFAULT_REGION='us-east-1'

# Celery variables
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

Run the setup

```
chmod +x setup.sh
sudo -E ./setup.sh
```

## Check ufw status

```
sudo ufw app list
sudo ufw allow 'Nginx HTTP'
```

### Reference

1. https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04
2. https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04
