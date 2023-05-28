import requests
import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
from bs4 import BeautifulSoup
from wordcloud import WordCloud

# Define the color palette
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

def scrape_imdb_movie_data():
    link = "https://www.imdb.com/search/title?release_date=2018-01-01,2018-12-31&sort=boxoffice_gross_us,desc&start="
    target_count = 100  # Set the number of movies you want to scrape

    movie_data = []
    page_number = 1

    while len(movie_data) < target_count:
        url = link + str(page_number)
        source = requests.get(url).text
        soup = BeautifulSoup(source, 'html.parser')
        movie_blocks = soup.find_all('div', class_='lister-item-content')

        for block in movie_blocks:
            title = block.find('a').text
            rating = block.find('strong').text
            genres = block.find('span', class_='genre').text.strip().split(', ')
            director = block.find('p', class_='').find_all('a')[0].text
            actors = [actor.text for actor in block.find('p', class_='').find_all('a')[1:]]

            movie_data.append({'Title': title, 'Rating': rating, 'Genres': genres, 'Director': director, 'Actors': actors})

        page_number += 1

    return movie_data


def create_top_rated_genres_bar_chart(movie_data):
    genre_ratings = {}

    for movie in movie_data:
        rating = float(movie['Rating'])
        for genre in movie['Genres']:
            if genre not in genre_ratings:
                genre_ratings[genre] = []
            genre_ratings[genre].append(rating)

    top_rated_genres = sorted(genre_ratings, key=lambda x: sum(genre_ratings[x]) / len(genre_ratings[x]), reverse=True)[:10]

    data = [
        go.Bar(
            x=top_rated_genres,
            y=[sum(genre_ratings[genre]) / len(genre_ratings[genre]) for genre in top_rated_genres],
            marker=dict(color='rgb(158,202,225)'),
            name='Average Rating'
        )
    ]

    layout = go.Layout(
        title='Top Rated Movies by Genre',
        xaxis=dict(title='Genre'),
        yaxis=dict(title='Average Rating')
    )

    fig = go.Figure(data=data, layout=layout)
    return fig


def create_favorite_directors_bar_chart(movie_data):
    director_ratings = {}

    for movie in movie_data:
        rating = float(movie['Rating'])
        director = movie['Director']
        if director not in director_ratings:
            director_ratings[director] = []
        director_ratings[director].append(rating)

    top_rated_directors = sorted(director_ratings, key=lambda x: sum(director_ratings[x]) / len(director_ratings[x]), reverse=True)[:10]

    data = [
        go.Bar(
            y=top_rated_directors,
            x=[sum(director_ratings[director]) / len(director_ratings[director]) for director in top_rated_directors],
            orientation='h',
            marker=dict(color='rgb(158,202,225)'),
            name='Average Rating'
        )
    ]

    layout = go.Layout(
        title='Favorite Movie Directors',
        xaxis=dict(title='Average Rating'),
        yaxis=dict(title='Director')
    )

    fig = go.Figure(data=data, layout=layout)
    return fig


def create_movie_ratings_scatter_plot(movie_data):
    movie_titles = [movie['Title'] for movie in movie_data]
    ratings = [float(movie['Rating']) for movie in movie_data]

    data = [
        go.Scatter(
            x=movie_titles,
            y=ratings,
            mode='markers',
            marker=dict(
                size=8,
                color=ratings,
                colorscale='Viridis',
                showscale=True
            ),
            name='Ratings'
        )
    ]

    layout = go.Layout(
        title='Movie Ratings',
        xaxis=dict(title='Movie Title'),
        yaxis=dict(title='Rating')
    )

    fig = go.Figure(data=data, layout=layout)
    return fig

def create_movie_titles_wordcloud(movie_data):
    movie_titles = [movie['Title'] for movie in movie_data]

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(movie_titles))

    data = go.Image(z=wordcloud.to_array())

    layout = go.Layout(title='Movie Titles Word Cloud')

    fig = go.Figure(data=data, layout=layout)
    return fig

def create_cumulative_rating_area_chart(movie_data):
    sorted_movies = sorted(movie_data, key=lambda x: x['Rating'], reverse=True)
    movie_titles = [movie['Title'] for movie in sorted_movies]
    ratings = [float(movie['Rating']) for movie in sorted_movies]

    cumulative_ratings = []
    cumulative_rating = 0

    for rating in ratings:
        cumulative_rating += rating
        cumulative_ratings.append(cumulative_rating)

    data = [
        go.Scatter(
            x=movie_titles,
            y=cumulative_ratings,
            mode='lines',
            fill='tozeroy',
            line=dict(color='rgb(158,202,225)'),
            name='Cumulative Rating'
        )
    ]

    layout = go.Layout(
        title='Cumulative Rating Over Time',
        xaxis=dict(title='Movie Title'),
        yaxis=dict(title='Cumulative Rating')
    )

    fig = go.Figure(data=data, layout=layout)
    return fig

def create_genre_distribution_pie_chart(movie_data):
    genre_counts = {}

    for movie in movie_data:
        for genre in movie['Genres']:
            if genre not in genre_counts:
                genre_counts[genre] = 0
            genre_counts[genre] += 1

    genre_labels = list(genre_counts.keys())
    genre_values = list(genre_counts.values())

    fig = go.Figure(data=[go.Pie(
        labels=genre_labels,
        values=genre_values,
        marker=dict(colors=colors),
        hoverinfo='label+percent',
        textinfo='value'
    )])

    fig.update_layout(
        title='Genre Distribution',
        showlegend=True
    )

    return fig



# Call the scraping function
movie_data = scrape_imdb_movie_data()

# Create the bar chart figure for top-rated genres
bar_chart_fig = create_top_rated_genres_bar_chart(movie_data)
genre_distribution_pie_chart_fig = create_genre_distribution_pie_chart(movie_data)
# Create the bar chart figure for favorite directors
directors_bar_chart_fig = create_favorite_directors_bar_chart(movie_data)

# Create the scatter plot figure for movie ratings
scatter_plot_fig = create_movie_ratings_scatter_plot(movie_data)

# Create the area chart figure for cumulative rating over time
area_chart_fig = create_cumulative_rating_area_chart(movie_data)



# Create a Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    children=[
        html.H1("Charts based on scrapping contents from IMDB "),
        dcc.Graph(
            id='bar-chart',
            figure=bar_chart_fig
        ),dcc.Graph(
            id='genre-distribution-pie-chart',
            figure=genre_distribution_pie_chart_fig

        ),dcc.Graph(
            id='wordcloud',
            figure=create_movie_titles_wordcloud(movie_data)
        ),dcc.Graph(
            id='directors-bar-chart',
            figure=directors_bar_chart_fig
        ),
        dcc.Graph(
            id='scatter-plot',
            figure=scatter_plot_fig
        ),
        dcc.Graph(
            id='area-chart',
            figure=area_chart_fig

        )
    ]
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
