# Fyyur - Find a Venue for Musicians

Artists and musical venues can use the app to find each other, and discover new music shows. It supports:

- creating new venues, artists, and creating new shows.
- searching for venues and artists.
- learning more about a specific artist or venue.

We want Fyyur to be the next new platform that artists and musical venues can use to find each other, and discover new music shows.

### Tech Stack

- **HTML**, **CSS**, and **Javascript** with Bootstrap 3 for the frontend
- **Python3** and **Flask** as our server language and server framework
- **PostgreSQL** for database
- **SQLAlchemy ORM** to be our ORM library of choice
- **Flask-Migrate** for creating and running schema migrations

### Development Setup

1. Create a virtual environment and install dependencies:

```bash
virtualenv --no-site-packages env
source env/bin/activate
pip install -r requirements.txt
```

2. Set environment variables in `config.py`, including the DB URI. Run the development server:

```bash
python3 app.py
```

3. Navigate to Home page [http://localhost:5000](http://localhost:5000)

### Database

#### Inserting Fixture Data

A script is provided to quickly populate fixture data.

```bash
python3 insert_mock_data.py
```

#### Migration

Database migration is set up with Flask-Migrate, which uses Alembic under the hood. It works with SQLAlchemy.

Run the following command to set up a migration folder.

```bash
flask db init
```

You can then generate an initial migration:

```bash
flask db migrate -m "Initial migration."
```

The migration scripts need to be reviewed and edited.

Apply the migration to the database:

```bash
flask db upgrade
```
