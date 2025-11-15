# Meetup Chat Application

A Django-based real-time chat application with WebSocket support for instant messaging.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up static files:
   ```bash
   python manage.py collectstatic
   ```

3. Start the server with WebSocket support:
   ```bash
   daphne mysite.asgi:application
   ```

4. Run tests:
   ```bash
   python manage.py test
   ```

## Default Admin Access

- **Username:** admin
- **Password:** 123456

## Development

### Database Updates
When modifying models, run:
```bash
python manage.py makemigrations Meetup
python manage.py migrate
```


## Notes

### For coursework - would not be in the actual Git repo:
- Create a `.env` file and fill in the file with the following:
```
DB_NAME=meetup_db
DB_USER=doadmin
DB_PASSWORD=
DB_HOST=itechteam73meetup-do-user-17948165-0.g.db.ondigitalocean.com
DB_PORT=25060

REDIS_HOST=team-73-redis-do-user-17948165-0.k.db.ondigitalocean.com
REDIS_PORT=25061
REDIS_USERNAME=default
REDIS_PASSWORD=

```

- Ensure Redis is running for WebSocket functionality
- Application uses Django Channels for real-time communication
- Static files are served using WhiteNoise in production

End of README.

