"""Importing the required libraries"""

from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd

# import plotly.offline as pyo
import plotly.graph_objs as go
import plotly.express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

"""Building the functions required to scrape the website"""


# ---------------------------------------------------------------------------

def get_country_data(country_line):
    """
    This function formats a given input line parsed from an html page.

    Parameters:
        country_line : str
            it is a row table row, that contains the data.

    Returns:
        line : list
            A list containing all the useful information retrieved.
    """
    import re
    line = country_line.strip().split("\n")
    line.pop(0)
    for i, element in zip(range(len(line)), line):
        if re.search("[1-9]+", element):
            line[i] = float(''.join(line[i].strip('+').split(",")))
        else:
            pass

    return line[:-1]


def get_column_names(tr):
    """
    This function return a well formatted list for the column names.
    """
    line = tr.strip("\n#").strip().split("\n")
    line[12] += line[13]
    line.pop(14)
    line.pop(13)
    return line[1:-1]


def scrape_corona_data():
    """
    This function scrapes the data from the target website and returns a well formatted dict that contains information about every given country.
    """
    from collections import \
        defaultdict  # Importing the defaultdict model, that will be used to store the information while scraping the website
    countries_data = defaultdict(dict)
    coronameter = requests.get(
        "https://www.worldometers.info/coronavirus/")  # requesting the index page from the server, it is also where our information resides
    bscorona = BeautifulSoup(coronameter.text, "lxml")  # parsing the webpage to a beautifulsoup object.
    corona_table = bscorona.find("table",
                                 id="main_table_countries_today")  # selecting the table where our data is contained.
    # print(corona_table.tr.text)
    column_names = get_column_names(corona_table.tr.text)
    # print(column_names)
    for tr in corona_table.find_all("tr", {"style": ""})[2:-2]:
        line = get_country_data(tr.text)
        countries_data[line[0]] = dict(zip(column_names, line[1:]))
    return countries_data


def replace_nan(data):
    """
    This function replaces empty or N/A values with np.nan so that it can be easier to manipulate the data later on.
    """
    for col in data.columns:
        data[col].replace(["N/A", "", " "], np.nan, inplace=True)


def create_clean_dataframe(countries_data):
    """
    This function takes a dict object and create a clean well formatted dataframe.

    Parameters:
        countries_data : dict object
            The dict that contains the countries data.
    Returns:
        data : dataframe
            Well formatted dataframe.
    """
    data = pd.DataFrame(countries_data).transpose()
    replace_nan(data)
    # Western Sahara is not a country
    data.loc['Western Sahara', :] = data.loc['Morocco', :]
    # data.drop(['Western Sahara'], inplace=True)
    # print(data.columns.values)
    return data


"""Building the plotting functions"""


# ---------------------------------------------------------------------------
# plot cases in map

def plot_country_map(data, keyword='TotalCases'):
    data_country = pd.DataFrame(zip(data.index, data[keyword]), columns=['Country', keyword])
    data_country[keyword].replace(np.nan, 0, inplace=True)
    fig = px.choropleth(data_country, color=keyword, locationmode='country names',
                        locations="Country", featureidkey="properties.district",
                        projection="mercator", scope='world', title='' + keyword + ' by countries'
                        )
    fig.update_geos(projection_type="natural earth")
    fig.update_layout(height=500, margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


# plot data for Morocco
import plotly.express as px

def plot_morocco_data(data):
    arab_countries = ['Morocco', 'Algeria', 'Tunisia', 'Egypt', 'Saudi Arabia','UAE','Qatar']  # Ajoutez les pays arabes souhaités
    cols = ["NewCases", "NewRecovered", "NewDeaths", "TotalCases", "TotalRecovered", "TotalDeaths"]
    data_country = data.loc[arab_countries, cols]
    fig = px.bar(data_country, arab_countries, y=cols, barmode='group')
    fig.update_layout(
        xaxis=dict(
            ticktext=["Morocco", "Algeria", "Tunisia", "Egypt", "Saudi Arabia","UAE","Qatar"],
            tickvals=arab_countries
        )
    )
    return fig


# plot data by country

def plot_pie_data(data, keyword='TotalCases'):
    data_country = pd.DataFrame(zip(data.index, data[keyword]), columns=['Country', keyword])
    # get the value of the 10th top-25 country
    sueil = data_country.nlargest(n=10, columns=[keyword])[keyword].iloc[-1]
    # Represent countries with low value with 'Other countries'
    data_country.loc[data_country[keyword] < sueil, 'Country'] = 'Other countries'  # Represent only large countries
    # print(data_country)
    fig = px.pie(data_country, values=keyword, names='Country', title='' + keyword + ' by countries')
    return fig


def plot_continent_data(data, keyword):
    """
    This function creates a Figure from continental data.

    Parameters:
        data : dataframe
            The whole dataset.
        keyword : str
            The keyword used to define the figure wanted, the available keyword : {"Total", "New"}

    Returns:
        fig : Figure
            The figure that will be drawed on plotly.
    """
    if keyword == "New":
        cols = ["NewCases", "NewRecovered", "NewDeaths"]
    else:
        cols = ["TotalCases", "TotalRecovered", "TotalDeaths"]
    # create a new dataframe with Continent and cols
    new_df = data[['Continent'] + cols]

    # use melt function to transform all cols in one column 'type' and all value in one column 'value
    df = pd.melt(new_df, id_vars=['Continent'], var_name='type', value_name='value')

    # plot new dataframe with plotly express, use color attribute to group
    fig = px.bar(df, x='Continent', y='value', color='type', barmode='group')

    return fig



def get_top_k_countries(data, k_countries=10, sortedby="TotalCases", ascending=False):
    """
    This function creates a k-len dataframe sorted by a key.

    Parameters:
        data : dataframe.
            The whole dataset.
        k_countries : int, Default=10
            The number of countries you want to plot.
        sortedby : str, Default="TotalCases".
            The column name we want to sort the data by
        ascending : Boolean, Default=False
            Either we want to sort in an ascending order or descending order.

    Returns:
        data : dataframe
            The k_contries lines dataframe sortedby the key given and in the wanted order.
    """
    return data.sort_values(by=sortedby, ascending=ascending).iloc[:k_countries]


def plot_top_k_countries(n_countries, sortby):
    """This function returns a figure where a number of countries are sorted by the value that resides in sortby."""
    res = get_top_k_countries(data, n_countries, sortby)
    # print('top k', res)
    fig = px.bar(res, x=res.index.to_list(), y=res[sortby])
    return fig


def plot_boxplots(data, keyword="Deaths/1M pop"):
    """This function returns a figure of the boxplot related to each continent in regards to the keyword."""
    data.groupby("Continent")
    fig = px.box(data, x="Continent", y=keyword, points="all")

    return fig


def init_figure():
    "This function initiate all the needed figure to start the app."
    return plot_country_map(data), \
           plot_morocco_data(data), \
           plot_pie_data(data), \
           plot_continent_data(data, keyword="New"), \
           plot_top_k_countries(10, "TotalCases"), plot_boxplots(data)


"""Initiale Figures"""
# ---------------------------------------------------------------------------

countries_data = scrape_corona_data()
data = create_clean_dataframe(countries_data)

init_map_fig, \
init_morocco_fig, \
init_pie_fig, \
init_continent_fig, \
init_k_countries_plot, \
init_box_fig = init_figure()

"""Building the app"""
# ---------------------------------------------------------------------------

# Initializing the app
app = dash.Dash(__name__)
server = app.server

# Building the app layout
app.layout = html.Div([
html.Div([
        html.Br(),
        html.H2("Cases attribute by countries (Map)", style={"text-align": "center"}),
        html.Br(),
        dcc.Dropdown(id="select_attribute_map",
                     options=[
                         dict(label="Total Cases", value='TotalCases'),
                         dict(label="New Cases", value='NewCases'),
                         dict(label="Total Deaths", value='TotalDeaths'),
                         dict(label="New Deaths", value='NewDeaths'),
                         dict(label="Total Recovered", value='TotalRecovered'),
                         dict(label="New Recovered", value='NewRecovered'),
                         dict(label="Active Cases", value='ActiveCases'),
                         dict(label="Serious, Critical Cases", value='Serious,Critical'),
                         dict(label="Total Tests", value='TotalTests')],
                     multi=False,
                     value="TotalCases",
                     style={"width": "60%"}
                     ),
    html.Br(),
    dcc.Graph(id="by_countries_map", figure=init_map_fig)
]),
    html.H1("Corona Tracker DashBoard", style={"text-align": "center"}),
    html.Br(),


    html.Div([
        html.Br(),
        html.H2("Cases in some Arab Countries", style={"text-align": "center"}),
        html.Br(),

        dcc.Graph(id="morocco_data", figure=init_morocco_fig)
    ]),


    html.Div([
        html.Br(),
        html.H2("Cases attribute by countries", style={"text-align": "center"}),
        html.Br(),
        dcc.Dropdown(id="select_attribute_pie",
                     options=[
                         dict(label="Total Cases", value='TotalCases'),
                         dict(label="New Cases", value='NewCases'),
                         dict(label="Total Deaths", value='TotalDeaths'),
                         dict(label="New Deaths", value='NewDeaths'),
                         dict(label="Total Recovered", value='TotalRecovered'),
                         dict(label="New Recovered", value='NewRecovered'),
                         dict(label="Active Cases", value='ActiveCases'),
                         dict(label="Serious, Critical Cases", value='Serious,Critical'),
                         dict(label="Total Tests", value='TotalTests')],
                     multi=False,
                     value="TotalCases",
                     style={"width": "60%"}
                     ),
        dcc.Graph(id="by_countries_pie", figure=init_pie_fig)
    ]),


    ])



# Defining the application callbacks
@app.callback(
    Output("by_countries_map", "figure"),
    Input("select_attribute_map", "value")
)
def update_map_data(value):
    return plot_country_map(data, keyword=value)


@app.callback(
    Output("morocco_data", "figure"),
    Input("select_attribute_morocco", "value")
)
def update_morocco_data(value):
    return plot_morocco_data(data, keyword=value)

@app.callback(
    Output("by_countries_pie", "figure"),
    Input("select_attribute_pie", "value")
)
def update_pie_data(value):
    return plot_pie_data(data, keyword=value)


@app.callback(
    Output("continent_corona_bar", "figure"),
    Input("select_keyword", "value")
)
def update_continent_corona_bar(value):
    return plot_continent_data(data, keyword=value)


@app.callback(
    Output("k_countries_sorted", "figure"),
    Input("select_k_countries", "value")
)
def update_k_countries_sorted(attribute, n_countries):
    return plot_top_k_countries(n_countries, attribute)


@app.callback(
    Output("continent_box_plot", "figure"),
    Input("select_box_attribute", "value")
)
def update_continent_box_plot(value):
    return plot_boxplots(data, keyword=value)


if __name__ == "__main__":
    countries_data = scrape_corona_data()
    data = create_clean_dataframe(countries_data)
    app.run_server()
