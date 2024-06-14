from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer(), nullable=False)
    description: Mapped[str] = mapped_column(String(80))
    rating: Mapped[float] = mapped_column(Float(), nullable=True)
    ranking: Mapped[int] = mapped_column(Integer(), nullable=True)
    review: Mapped[str] = mapped_column(String(30), nullable=True)
    img_url: Mapped[str] = mapped_column(String(30))



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6c'
Bootstrap5(app)

class SearchMovie():
    API_RAC = 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ZWY1YTAyZjY1YzVmMGZiODQ3ZTNjMjA4ZDk2ZGEyYyIsInN1YiI6IjY2NjkxYzZjZjRmMmNlMjllN2ZkMTU2OSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.wPLX_dPEkjE8WuEXoltngfhd2RmtVViPbmLu3cN7ruc'

    def __init__(self):
        self.url = "https://api.themoviedb.org/3/authentication"
        self.headers = {
            "accept": "application/json",
            "Authorization": SearchMovie.API_RAC
        }


    def search(self, movie: str) -> list:
        url = 'https://api.themoviedb.org/3/search/movie'
        parameters = {
            'query': movie,
            'include_adult':True,
            'page':1
        }
        response = requests.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        data = response.json()
        movies = data['results']
        movies = [movie for movie in movies]
        return movies
    def get_details(self, movie_id: int) -> dict:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}'

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        details = {
            'movie_title': data['original_title'],
            'movie_year': data['release_date'][:4],
            'description': data['overview'],
            'img_path': f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        }
        return details


class EditMovie(FlaskForm):
    rating = StringField('What is your rating out of 10?', validators=[DataRequired()])
    review = StringField('What is your review?', validators=[DataRequired()])
    submit = SubmitField('Done')


class DeleteMovie(FlaskForm):
    back = SubmitField('Back')
    delete = SubmitField('Delete')

class AddMovie(FlaskForm):
    movie_title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Add')


@app.route('/')
def index():
    all_movies = Movie.query.order_by(desc(Movie.rating)).all()
    for i ,movie in enumerate(all_movies, start=1):
        with app.app_context():
            movie.ranking = i
            db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route("/<id>")
def home(id):
    all_movies = Movie.query.order_by(desc(Movie.rating)).all()
    count = int(id) - 1
    movie = all_movies[count]
    print(movie.title)
    return render_template("index.html", movie=movie)


@app.route("/edit/<id>", methods=['GET', 'POST'])
def update_movie(id):
    update_form = EditMovie()
    if request.method == 'POST' and update_form.validate_on_submit():
        with app.app_context():
            movie_id = id
            rating = update_form.rating.data
            review = update_form.review.data
            updated_movie = db.get_or_404(Movie, movie_id)
            updated_movie.rating = rating
            updated_movie.review = review
            db.session.commit()
        return redirect(url_for('index'))
    movie_id = id
    updated_movie = db.get_or_404(Movie, movie_id)
    return render_template("edit.html", movie=updated_movie, form=update_form)


@app.route("/delete/<id>", methods=['GET', 'POST'])
def delete_movie(id):
    delete_form = DeleteMovie()
    movie_id = id
    if request.method == 'POST' and delete_form.validate_on_submit() and delete_form.delete.data:
        with app.app_context():
            movie_to_delete = db.get_or_404(Movie, movie_id)
            db.session.delete(movie_to_delete)
            db.session.commit()
        return redirect(url_for('index'))

    elif delete_form.back.data:
        return redirect(url_for('home', id=movie_id))

    movie_to_delete = db.get_or_404(Movie, movie_id)
    return render_template("delete.html", movie=movie_to_delete, form=delete_form)


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    add_form = AddMovie()
    if request.method == "POST" and add_form.validate_on_submit():
        movie_title = add_form.movie_title.data
        adding_movie = SearchMovie()
        movie_query = adding_movie.search(movie_title)
        return render_template('select.html', movielist=movie_query)

    return render_template("add.html", form=add_form)


@app.route("/find/id", methods=['GET', 'POST'])
def find():
    id = request.args.get('id')
    movie_details = SearchMovie().get_details(int(id))
    movie = Movie(
        title=movie_details['movie_title'],
        year=movie_details['movie_year'],
        rating=0,
        ranking=0,
        review='',
        description=movie_details['description'],
        img_url=movie_details['img_path']
    )
    db.session.add(movie)
    db.session.commit()
    return redirect(url_for('update_movie', id=movie.id))


if __name__ == '__main__':
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-ten-movies-collection.db"
    # initialize the app with the extension
    db.init_app(app)
    with app.app_context():
        second_movie = Movie(
            title="Avatar The Way of Water",
            year=2022,
            description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
            rating=7.3,
            ranking=9,
            review="I liked the water.",
            img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
        )
        # db.session.add(second_movie)
        # db.session.commit()
        db.create_all()

    app.run(debug=True)
