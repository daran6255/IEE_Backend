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
```

Run the setup

```
chmod +x setup.sh
sudo -E ./setup.sh
```
