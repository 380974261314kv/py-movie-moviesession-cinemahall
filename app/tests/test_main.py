import pytest
import datetime

from contextlib import redirect_stdout
from io import StringIO

from ..main import (
    Actor,
    Genre,
    Movie,
    CinemaHall,
    MovieSession,
    MovieService,
    CinemaHallService,
    MovieSessionService
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title,description,out",
    [
        ("Speed", "Action movie", "Speed\n"),
        ("Harry Potter", "Magic movie", "Harry Potter\n"),
        ("Batman", "Superhero movie", "Batman\n"),
    ]
)
def test_movie_str(title, description, out):
    movie = Movie.objects.create(title=title, description=description)

    f = StringIO()

    with redirect_stdout(f):
        print(movie)

    output = f.getvalue()

    assert out == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,rows,seats_in_row,out",
    [
        ("VIP", 12, 10, "VIP\n"),
        ("Blue", 8, 11, "Blue\n"),
        ("Cheap", 7, 17, "Cheap\n"),
    ]
)
def test_cinema_hall_str(name, rows, seats_in_row, out):
    cinema_hall = CinemaHall.objects.create(name=name,
                                            rows=rows,
                                            seats_in_row=seats_in_row)

    f = StringIO()

    with redirect_stdout(f):
        print(cinema_hall)

    output = f.getvalue()

    assert out == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,rows,seats_in_row,capacity",
    [
        ("VIP", 12, 10, 120),
        ("Blue", 8, 11, 88),
        ("Cheap", 7, 17, 119),
    ]
)
def test_cinema_hall_capacity(name, rows, seats_in_row, capacity):
    cinema_hall = CinemaHall.objects.create(name=name,
                                            rows=rows,
                                            seats_in_row=seats_in_row)

    assert cinema_hall.capacity() == capacity


@pytest.fixture()
def movie_session_database_data():
    movie_sessions = []
    movie = Movie.objects.create(title="Speed",
                                 description="None")
    cinema_hall = CinemaHall.objects.create(name="Blue",
                                            rows=10,
                                            seats_in_row=10)
    movie_sessions.append((MovieSession.objects.create(
        show_time=datetime.datetime(2022, 2, 22, 15, 30),
        cinema_hall=cinema_hall,
        movie=movie
    ), "Speed 2022-02-22 15:30:00\n"))

    movie = Movie.objects.create(title="Harry Potter",
                                 description="None")

    movie_sessions.append((MovieSession.objects.create(
        show_time=datetime.datetime(2021, 2, 23, 11, 10),
        cinema_hall=cinema_hall,
        movie=movie
    ), "Harry Potter 2021-02-23 11:10:00\n"))

    return movie_sessions


@pytest.mark.django_db
def test_movie_session_str(movie_session_database_data):
    for data in movie_session_database_data:
        f = StringIO()

        with redirect_stdout(f):
            print(data[0])

        output = f.getvalue()

        assert output == data[1]


@pytest.fixture()
def database_data():
    action = Genre.objects.create(name="Action")
    drama = Genre.objects.create(name="Drama")
    western = Genre.objects.create(name="Western")

    reeves = Actor.objects.create(first_name="Keanu", last_name="Reeves")
    johansson = Actor.objects.create(first_name="Scarlett",
                                     last_name="Johansson")
    clooney = Actor.objects.create(first_name="George", last_name="Clooney")

    matrix = Movie.objects.create(title="Matrix", description="Matrix movie")
    matrix.actors.add(reeves)
    matrix.actors.add(johansson)
    matrix.genres.add(action)

    batman = Movie.objects.create(title="Batman", description="Batman movie")
    batman.genres.add(drama)
    batman.actors.add(clooney)

    titanic = Movie.objects.create(title="Titanic",
                                   description="Titanic movie")
    titanic.genres.add(drama, action)

    good_bad = Movie.objects.create(
        title="The Good, the Bad and the Ugly",
        description="The Good, the Bad and the Ugly movie"
    )
    good_bad.genres.add(western)

    blue = CinemaHall.objects.create(name="Blue", rows=10, seats_in_row=12)
    vip = CinemaHall.objects.create(name="VIP", rows=4, seats_in_row=6)
    cheap = CinemaHall.objects.create(name="Cheap", rows=15, seats_in_row=27)

    MovieSession.objects.create(
        show_time=datetime.datetime(2019, 8, 19, 20, 30),
        cinema_hall=blue,
        movie=matrix
    )
    MovieSession.objects.create(
        show_time=datetime.datetime(2017, 8, 19, 11, 10),
        cinema_hall=cheap,
        movie=titanic
    )
    MovieSession.objects.create(
        show_time=datetime.datetime(2021, 4, 3, 13, 50),
        cinema_hall=vip,
        movie=good_bad
    )

    MovieSession.objects.create(
        show_time=datetime.datetime(2021, 4, 3, 16, 30),
        cinema_hall=cheap,
        movie=matrix
    )


@pytest.mark.django_db
def test_movie_service_get_movies(database_data):
    assert list(MovieService.get_movies().values_list(
        "title", "description"
    )) == [
        ("Matrix", "Matrix movie"),
        ("Batman", "Batman movie"),
        ("Titanic", "Titanic movie"),
        ("The Good, the Bad and the Ugly",
         "The Good, the Bad and the Ugly movie")
    ]


@pytest.mark.django_db
def test_movie_service_get_movie_by_id(database_data):
    assert MovieService.get_movie_by_id(1).title == "Matrix"
    assert MovieService.get_movie_by_id(1).description == "Matrix movie"
    assert MovieService.get_movie_by_id(3).title == "Titanic"
    assert MovieService.get_movie_by_id(3).description == "Titanic movie"


@pytest.mark.django_db
def test_movie_service_get_movie_by_genres_and_actors(database_data):
    assert list(MovieService.get_movies_by_genres_and_actors(
        [1, 2], [2, 3]
    ).values_list("title")) == [("Matrix", ), ("Batman", )]
    assert list(MovieService.get_movies_by_genres_and_actors(
        [1, 3], [1, 3]
    ).values_list("title")) == [("Matrix", )]


@pytest.mark.django_db
def test_movie_service_get_movie_by_genres_and_no_actors(database_data):
    assert list(MovieService.get_movies_by_genres_and_actors(
        genres_ids=[1]
    ).values_list("title")) == [("Matrix", ), ("Titanic",)]
    assert list(MovieService.get_movies_by_genres_and_actors(
        genres_ids=[2, 3]
    ).values_list("title")) == [
        ("Batman",),
        ("Titanic",),
        ("The Good, the Bad and the Ugly",)
    ]


@pytest.mark.django_db
def test_movie_service_get_movie_by_actors_and_no_genres(database_data):
    assert list(MovieService.get_movies_by_genres_and_actors(
        actors_ids=[1]
    ).values_list("title")) == [("Matrix", )]
    assert list(MovieService.get_movies_by_genres_and_actors(
        actors_ids=[2, 3]
    ).values_list("title")) == [
        ("Matrix",),
        ("Batman",),
    ]


@pytest.mark.django_db
def test_movie_service_create_movie():
    MovieService.create_movie(movie_title="Matrix",
                              movie_description="Matrix description")
    MovieService.create_movie(movie_title="Batman",
                              movie_description="Batman description")
    assert list(Movie.objects.all().values_list(
        "title", "description"
    )) == [("Matrix", "Matrix description"), ("Batman", "Batman description")]


@pytest.mark.django_db
def test_cinema_hall_service_get_cinema_halls(database_data):
    assert list(CinemaHallService.get_cinema_halls().values_list(
        "name", "rows", "seats_in_row"
    )) == [("Blue", 10, 12), ("VIP", 4, 6), ("Cheap", 15, 27)]


@pytest.mark.django_db
def test_cinema_hall_service_create_cinema_hall():
    CinemaHallService.create_cinema_hall(hall_name="Blue",
                                         hall_rows=10,
                                         hall_seats_in_row=12)
    CinemaHallService.create_cinema_hall(hall_name="VIP",
                                         hall_rows=3,
                                         hall_seats_in_row=5)
    CinemaHallService.create_cinema_hall(hall_name="Cheap",
                                         hall_rows=18,
                                         hall_seats_in_row=11)
    assert list(CinemaHall.objects.all().values_list(
        "name", "rows", "seats_in_row"
    )) == [("Blue", 10, 12), ("VIP", 3, 5), ("Cheap", 18, 11)]


@pytest.mark.django_db
def test_movie_session_service_get_movies_sessions(database_data):
    assert list(MovieSessionService.get_movies_sessions().values_list(
        "show_time__date", "cinema_hall__name", "movie__title"
    )) == [
        (datetime.date(2019, 8, 19), "Blue", "Matrix"),
        (datetime.date(2017, 8, 19), "Cheap", "Titanic"),
        (datetime.date(2021, 4, 3), "VIP", "The Good, the Bad and the Ugly"),
        (datetime.date(2021, 4, 3), 'Cheap', 'Matrix'),
    ]


@pytest.mark.django_db
def test_movie_session_service_get_movie_session_by_id(database_data):
    session_1 = MovieSessionService.get_movie_session_by_id(1)
    assert session_1.show_time.date() == datetime.date(2019, 8, 19)
    assert session_1.movie.title == "Matrix"
    assert session_1.cinema_hall.name == "Blue"

    session_3 = MovieSessionService.get_movie_session_by_id(3)
    assert session_3.show_time.date() == datetime.date(2021, 4, 3)
    assert session_3.movie.title == "The Good, the Bad and the Ugly"
    assert session_3.cinema_hall.name == "VIP"


@pytest.mark.django_db
def test_movie_session_service_get_movie_session_by_date(database_data):
    sessions_1 = MovieSessionService.get_movies_sessions_by_date("2019-8-19")
    assert list(sessions_1.values_list(
        "movie__title", "cinema_hall__name"
    )) == [("Matrix", "Blue")]

    sessions_2 = MovieSessionService.get_movies_sessions_by_date("2021-4-3")
    assert list(sessions_2.values_list(
        "movie__title", "cinema_hall__name"
    )) == [
        ("The Good, the Bad and the Ugly", "VIP"),
        ("Matrix", "Cheap"),
    ]


@pytest.mark.django_db
def test_movie_session_service_delete_movie_session_by_id(database_data):
    MovieSessionService.delete_movie_session_by_id(1)
    MovieSessionService.delete_movie_session_by_id(4)

    assert list(MovieSessionService.get_movies_sessions().values_list(
        "show_time__date", "cinema_hall__name", "movie__title"
    )) == [
        (datetime.date(2017, 8, 19), "Cheap", "Titanic"),
        (datetime.date(2021, 4, 3), "VIP", "The Good, the Bad and the Ugly"),
    ]
