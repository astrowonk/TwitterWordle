import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import dash_dataframe_table
from sqlalchemy import create_engine
from first_word import map_to_emoji, wordle_lookup
from helper import make_freqs, flatten_columns
from ast import literal_eval

import pandas as pd
pd.DataFrame.flatten_columns = flatten_columns
import numpy as np
pd.options.plotting.backend = 'plotly'

sql_db = create_engine('sqlite:///wordle_first_words.db')

all_guesses = pd.read_sql("select distinct guess from main; ",
                          sql_db)['guess'].sort_values().tolist()

all_numbers = pd.read_sql(
    "select distinct wordle_num from main; ",
    sql_db)['wordle_num'].sort_values().astype(int).tolist()

app = Dash(__name__,
           external_stylesheets=[dbc.themes.YETI],
           suppress_callback_exceptions=True,
           url_base_pathname='/dash/wordle_openers/',
           title="Wordle Opener Explorer")

server = app.server

main_content = [
    html.Div(children=[
        dbc.Label("Choose Wordle Opener for Day by Day Graph...",
                  html_for="guess-dropdown"),
        dcc.Dropdown(
            options=[{
                'value': x,
                'label': x
            } for x in all_guesses],
            value='adieu',
            id='guess-dropdown',
            clearable=False,
            persistence=True,
        )
    ]),
    html.Div(id='graph-row'),
    html.Div(id='detail-row')
]

left_sidebar = [
    dbc.Label("Max Guesses for Pattern", html_for="max-guess-count"),
    dbc.Input(id='max-guess-count',
              placeholder='max guess count',
              type='number',
              value=150,
              persistence=True,
              min=0,
              max=7000),
    dbc.Label("Min Number of Valid Points", html_for="min-data-count"),
    dbc.Input(id='min-data-count',
              placeholder='min data count',
              type='number',
              value=7,
              persistence=True,
              min=0,
              max=len(all_numbers)),
    dbc.Tooltip(
        "Filter out data points where the number of guesses that could create that score pattern exceed this number.",
        target='max-guess-count'),
    dbc.Tooltip(
        "Filter out words where the number of remaining data points is less than this number.",
        target='min-data-count'),
    dbc.Label("Set wordle number range to include for analysis",
              html_for='wordle-num-range'),
    dcc.RangeSlider(min=min(all_numbers),
                    max=max(all_numbers),
                    value=[min(all_numbers),
                           max(all_numbers)],
                    id='wordle-num-range',
                    marks={x: str(x)
                           for x in all_numbers[::3]},
                    persistence=False),
    dbc.Spinner(html.Div(id='top-table-row'))
]

intro_text = """
## Wordle First Guess Explorer

For any given wordle answer, a wordle opener would produce a specific score pattern. The popularity of that pattern for each day is shown on the graph.
Rank 1 means it was the most popular pattern that day. Guess count is how many *other* guess words would have produced the same pattern. If the guess count is very high, then it is likely the high rank is driven not by any one word.

`Max Guesses for Pattern` removes data points from the calculation for **Top Wordle Openers** due to too many other words that could make the opening score pattern. These marked with an **X** in the scatter plot.

The `Min number of Valid Points` parameter sets the minimum number of circle points needed to be considered for the top list. 

This dashboard relies on Ben Hamner's [Wordle Tweets sample data set on Kaggle](https://www.kaggle.com/benhamner/wordle-tweets).


"""

app.layout = dbc.Container(
    children=[
        dbc.Row(id='intro', children=dbc.Col(dcc.Markdown(intro_text))),
        dbc.Row(children=[
            dbc.Col(id="left-sidebar", children=left_sidebar),
            dbc.Col(id='main-content', children=main_content),
        ])
    ],
    style={'padding': '80px'},
    fluid=True,
)


@app.callback(
    Output("graph-row", "children"),
    Input("guess-dropdown", "value"),
    Input('max-guess-count', 'value'),
    Input('wordle-num-range', 'value'),
)
def make_graph(guess, max_guess_count, wordle_range):
    mean_score = pd.read_sql(
        f"select avg(score_frequency_rank) from main where guess = {guess!r} and score <> '00000'",
        con=sql_db).iloc[0, 0]

    plot_data = pd.read_sql(f"select * from main where guess = {guess!r}",
                            con=sql_db)

    plot_data['valid_flag'] = (plot_data['guess_count'] <=
                               max_guess_count).astype(int)
    plot_data['pattern'] = plot_data['score'].map(map_to_emoji)
    myplot = plot_data.sort_values('wordle_num').plot.scatter(
        x='wordle_num',
        y='score_frequency_rank',
        hover_data=['pattern'],
        custom_data=['score'],
        color='guess_count',
        symbol='valid_flag',
        color_continuous_scale='bluered',
        symbol_map={
            0: 'x',
            1: 'circle'
        },
        title=f'{guess.upper()} Possible Popularity, Mean {mean_score:.2f}',
        labels={
            'score_frequency_rank': "Score Pattern Frequency Rank",
            'valid_flag': 'Meets Guess Count Threshold'
        }
        # color_continuous_scale='thermal',
    )
    myplot.update_traces(marker={'size': 10})
    myplot.update_xaxes(range=[wordle_range[0] - 1, wordle_range[1] + 1])

    myplot.update_yaxes(autorange="reversed")
    myplot.update_layout(legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    return [dcc.Graph(figure=myplot, id='guess-graph')]


@app.callback(Output("detail-row", 'children'),
              Input('guess-graph', 'clickData'),
              State('guess-dropdown', 'value'),
              prevent_initial_call=True)
def make_detail(clickData, guess):
    print(clickData)
    if not clickData:
        return dash.no_update
    score = clickData['points'][0]['customdata'][0]
    pattern = clickData['points'][0]['customdata'][1]
    wordle_num = clickData['points'][0]['x']
    print(score, wordle_num)

    df = pd.read_sql(
        f"select guess,commonality from main where score = {score!r} and wordle_num = {wordle_num} and commonality > 0 order by commonality DESC",
        con=sql_db)

    answer = wordle_lookup.get(wordle_num)
    return [
        html.
        P(f'{len(df)} guesses with pattern {pattern} for Wordle {wordle_num} and answer {answer.upper()}'
          ),
        dbc.Table.from_enhanced_dataframe(df.head(min(50, df.shape[0])))
    ]


@app.callback(Output("top-table-row", 'children'),
              Input('max-guess-count', 'value'),
              Input('min-data-count', 'value'),
              Input('wordle-num-range', 'value'),
              prevent_initial_call=False)
def make_leader_table(max_guess_count, min_data_count, wordle_num_range):
    wmin, wmax = wordle_num_range

    # first_guess_list.query(
    #     'score != "00000" and @wmin <= wordle_num <= @wmax')
    # top_list_data['max_score'] = top_list_data.groupby(
    #     'guess')['score_frequency_rank'].transform(max)
    # top_list_data = top_list_data.query('guess_count <= @max_guess_count')
    return dbc.Col([
        html.H5("Estimated Top Wordle Openers"),
        dbc.Table.from_enhanced_dataframe(
            pd.read_sql(
                f"""select guess, AVG(weighted_rank) as weighted_rank_mean ,count(weighted_rank) as 
 weighted_rank_count from main where score <> '00000'  
 and guess_count <= {max_guess_count} and wordle_num between {wmin} and {wmax}  group by guess having weighted_rank_count >= {min_data_count} order by weighted_rank_mean limit 25; """,
                sql_db),
            button_columns=['guess'],
        )
    ])


@app.callback(Output("guess-dropdown", 'value'),
              Input({
                  'type': 'guess-button',
                  'index': ALL
              }, 'n_clicks'),
              prevent_initial_call=True)
def process_buttons(value):
    if not value:
        return dash.no_update
    if dash.callback_context.triggered:
        print(dash.callback_context.triggered)
        theguess = literal_eval(dash.callback_context.triggered[0]
                                ['prop_id'].split('.')[0])['index']
        print(theguess)
        return (theguess)
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
