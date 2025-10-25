# Docker Setup for News Addiction Django Project

This guide explains how to run the News Addiction Django project using Docker.

## Prerequisites

- Docker installed on your system

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd news_addiction
   ```

2. **Update the environment file to contain your secrets :**
   ```bash
   .env
   ```
   
   **Note:** Update the `.env` file with your actual secret key and other configuration as needed.

3. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

4. **The application will be available at:**
   - Django application: http://localhost:8000
   - MySQL database: localhost:3306

## Environment Configuration

The project uses environment variables for configuration.  
modify `.env` as needed:

```bash
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=1
DB_ENGINE=django.db.backends.mysql
DB_NAME=news_addiction_db
DB_USER=news_user
DB_PASSWORD=news_password
DB_HOST=db
DB_PORT=3306
```

## Docker Commands

### Build the Docker image:
```bash
docker-compose build
```

### Start the services:
```bash
docker-compose up
```

### Start services in background:
```bash
docker-compose up -d
```

### Stop the services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs
```

### Run Django management commands:
**Note:** As per the docker-compose.yml file, management commands to migrate and setup test users are run automatically when building the docker image.


```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic

# Run custom management commands
docker-compose exec web python manage.py create_test_users
```

## Database Management

The MySQL database data is persisted in a Docker volume. To reset the database:

```bash
# Stop services
docker-compose down

# Remove the database volume
docker volume rm news_addiction_mysql_data

# Start services again
docker-compose up
```

## Production Considerations

For production deployment:

1. **Update environment variables:**
   - Set `DEBUG=0`
   - Use a strong, unique `SECRET_KEY`
   - Configure proper database credentials
   - Set appropriate `ALLOWED_HOSTS`

2. **Use a production WSGI server:**
   - Replace the development server with Gunicorn or uWSGI
   - Add a reverse proxy like Nginx

3. **Security:**
   - Use Docker secrets for sensitive data
   - Configure proper network security
   - Use HTTPS

## Troubleshooting

### Database Connection Issues:
- Ensure the database service is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`

### Permission Issues:
- Ensure Docker has proper permissions
- On Linux, you might need to adjust file ownership

### Port Conflicts:
- If port 8000 or 3306 are already in use, modify the ports in `docker-compose.yml`

### Static Files Issues:
- Run `docker-compose exec web python manage.py collectstatic`
 **Note:** - This command is automatically run when building the docker object.
## File Structure

```
news_addiction/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml        # Multi-container setup
├── .dockerignore             # Files to exclude from Docker build
├── .env                      # Template environment file
├── requirements.txt          # Python dependencies
└── ...                       # Other project files
```

## Development Workflow

For development with Docker:

1. Make code changes in your local files
2. The changes are automatically reflected in the container (volume mounting)
3. Restart the service if needed: `docker-compose restart web`

For database schema changes:
1. Make model changes
2. Create migrations: `docker-compose exec web python manage.py makemigrations`
3. Apply migrations: `docker-compose exec web python manage.py migrate`