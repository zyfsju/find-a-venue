# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm as Form
from forms import *
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Venue {self.id} {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Artist {self.id} {self.name}>"


class Show(db.Model):
    __tablename__ = "Show"

    venue_id = db.Column(
        "venue_id", db.Integer, db.ForeignKey("Venue.id"), primary_key=True
    )
    artist_id = db.Column(
        "artist_id", db.Integer, db.ForeignKey("Artist.id"), primary_key=True
    )
    start_time = db.Column(db.DateTime, primary_key=True)
    venue = db.relationship("Venue", foreign_keys="Show.venue_id", backref="shows")
    artist = db.relationship("Artist", foreign_keys="Show.artist_id", backref="shows")

    def __repr__(self):
        return f"<Show {self.venue_id} {self.artist_id} {self.start_time}>"


def sa_obj_to_dict(sa_obj):

    return {c.name: getattr(sa_obj, c.name) for c in sa_obj.__class__.__table__.columns}


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    if not isinstance(value, str):
        value = value.strftime("%m/%d/%Y, %H:%M:%S")
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    venues = Venue.query.all()
    for city, state in list(set((v.city, v.state) for v in venues)):
        row = {
            "city": city,
            "state": state,
            "venues": [
                {"id": v.id, "name": v.name,}
                for v in venues
                if v.city == city and v.state == state
            ],
        }
        data.append(row)
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    data = [{"id": v.id, "name": v.name} for v in venues]
    response = {"count": len(data), "data": data}
    return render_template(
        "pages/search_venues.html", results=response, search_term=search_term,
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    if not venue:
        return not_found_error("error")
    shows = [
        {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time,
        }
        for show in venue.shows
    ]
    past_shows = list(filter(lambda x: x.get("start_time") < datetime.now(), shows))
    upcoming_shows = list(
        filter(lambda x: x.get("start_time") >= datetime.now(), shows)
    )
    # print(past_shows)
    data = {
        # **{x.name: getattr(venue, x.name) for x in Venue.__table__.columns},
        **sa_obj_to_dict(venue),
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(set(x.get("artist_id") for x in past_shows)),
        "upcoming_shows_count": len(set(x.get("artist_id") for x in upcoming_shows)),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    data = request.form or {}
    kwargs = {k: v for k, v in data.items() if k in Venue.__table__.columns}
    kwargs.update(
        {"genres": data.getlist("genres"), "seeking_talent": True if "y" else False}
    )
    existed = (
        Venue.query.filter_by(name=kwargs.get("name"))
        .filter_by(city=kwargs.get("city"))
        .filter_by(state=kwargs.get("state"))
        .first()
    )
    if existed:
        flash("Venue " + data.get("name") + " is already listed.")
    else:
        try:
            new_venue = Venue(**kwargs)
            db.session.add(new_venue)
            db.session.commit()
            # on successful db insert, flash success
            flash("Venue " + data.get("name") + " was successfully listed!")
        except Exception as e:
            db.session.rollback()
            raise e
            flash(
                "An error occurred. Venue " + data.get("name") + " could not be listed."
            )
        finally:
            db.session.close()
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + venue.name + " was successfully deleted.")
    except:
        db.session.rollback()
        flash("An error occurred. Venue " + venue.name + " could not be deleted.")
    finally:
        db.session.close()

    return render_template("pages/home.html")


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    data = [{"id": a.id, "name": a.name} for a in artists]
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():

    search_term = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    data = [{"id": a.id, "name": a.name} for a in artists]
    response = {"count": len(data), "data": data}
    return render_template(
        "pages/search_artists.html", results=response, search_term=search_term,
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return not_found_error("error")
    shows = [
        {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time,
        }
        for show in artist.shows
    ]
    past_shows = list(filter(lambda x: x.get("start_time") < datetime.now(), shows))
    upcoming_shows = list(
        filter(lambda x: x.get("start_time") >= datetime.now(), shows)
    )
    # print(past_shows)
    data = {
        # **{x.name: getattr(venue, x.name) for x in Venue.__table__.columns},
        **sa_obj_to_dict(artist),
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(set(x.get("venue_id") for x in past_shows)),
        "upcoming_shows_count": len(set(x.get("venue_id") for x in upcoming_shows)),
    }
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if not artist:
        return not_found_error("error")
    artist = sa_obj_to_dict(artist)
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    artist = Artist.query.get(artist_id)
    if not artist:
        return not_found_error("error")
    artist_name = artist.name
    data = request.form or {}
    try:
        kwargs = {k: v for k, v in data.items() if k in Artist.__table__.columns}
        kwargs.update({"genres": data.getlist("genres")})
        db.session.query(Artist).filter(Artist.id == artist_id).update(
            kwargs, synchronize_session=False
        )
        db.session.commit()
        # on successful db insert, flash success
        flash("Artist " + data.get("name") + " was successfully updated!")
    except Exception as e:
        db.session.rollback()
        raise e
        flash("An error occurred. Artist " + artist_name + " could not be updated.")
    finally:
        db.session.close()
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if not venue:
        return not_found_error("error")
    venue = sa_obj_to_dict(venue)
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    if not venue:
        return not_found_error("error")
    venue_name = venue.name
    data = request.form or {}
    try:
        kwargs = {k: v for k, v in data.items() if k in Venue.__table__.columns}
        kwargs.update({"genres": data.getlist("genres")})
        db.session.query(Venue).filter(Venue.id == venue_id).update(
            kwargs, synchronize_session=False
        )
        db.session.commit()
        # on successful db insert, flash success
        flash("Venue " + data.get("name") + " was successfully updated!")
    except Exception as e:
        db.session.rollback()
        raise e
        flash("An error occurred. Venue " + venue_name + " could not be updated.")
    finally:
        db.session.close()
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    data = request.form or {}
    kwargs = {k: v for k, v in data.items() if k in Artist.__table__.columns}
    kwargs.update(
        {
            "genres": data.getlist("genres"),
            "seeking_venue": True if data.get("seeking_venue") == "y" else False,
        }
    )
    existed = (
        Artist.query.filter_by(name=kwargs.get("name"))
        .filter_by(city=kwargs.get("city"))
        .filter_by(state=kwargs.get("state"))
        .first()
    )
    if existed:
        flash("Venue " + data.get("name") + " is already listed.")
    try:
        new_artist = Artist(**kwargs)
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash("Artist " + request.form["name"] + " was successfully listed!")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred. Artist " + data.get("name") + " could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    shows = Show.query.all()
    data = [
        {
            **sa_obj_to_dict(sh),
            "venue_name": sh.venue.name,
            "artist_name": sh.artist.name,
            "artist_image_link": sh.artist.image_link,
        }
        for sh in shows
    ]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    data = request.form or {}
    try:
        kwargs = {k: v for k, v in data.items() if k in Show.__table__.columns}
        new_show = Show(**kwargs)
        db.session.add(new_show)
        db.session.commit()
        # on successful db insert, flash success
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
