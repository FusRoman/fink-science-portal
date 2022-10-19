import pandas as pd
import numpy as np
import io
import requests
import random

from app import app
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, dash_table, State
import dash_mantine_components as dmc

from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify

from apps.utils import markdownify_objectid, random_color

import plotly.graph_objs as go
import plotly.express as px


@app.callback(Output("pdf_lc", "data"), [Input("url", "pathname")])
def store_lighcurves_query(name):
    """Cache query results (sso trajectories and lightcurves) for easy re-use

    https://dash.plotly.com/sharing-data-between-callbacks
    """

    r_lc = requests.post(
        "https://fink-portal.org/api/v1/ssocand",
        json={
            "kind": "lightcurves",  # Mandatory, `orbParams` or `lightcurves`
        },
    )

    # Format output in a DataFrame
    pdf_lc = pd.read_json(io.BytesIO(r_lc.content)).drop_duplicates("d:candid")

    return pdf_lc.to_json()


@app.callback(Output("pdf_orb", "data"), [Input("pdf_lc", "data")])
def store_orbit_query(json_lc):
    """Cache query results (sso trajectories and lightcurves) for easy re-use

    https://dash.plotly.com/sharing-data-between-callbacks
    """

    pdf_lc = pd.read_json(json_lc)

    r_orb = requests.post(
        "https://fink-portal.org/api/v1/ssocand",
        json={
            "kind": "orbParams",  # Mandatory, `orbParams` or `lightcurves`
        },
    )

    # Format output in a DataFrame
    pdf_orb = pd.read_json(io.BytesIO(r_orb.content)).drop_duplicates(
        ["d:a", "d:e", "d:i"]
    )
    pdf_orb = pdf_orb[pdf_orb["d:trajectory_id"].isin(pdf_lc["d:trajectory_id"])]

    return pdf_orb.to_json()


@app.callback(Output("mpc_data", "data"), [Input("url", "pathname")])
def load_mpc(url):

    mpc_ae = pd.read_parquet("data/ae_mpc.parquet")
    return mpc_ae.to_json()


def populate_sso_table(data, columns):
    """Define options of the results table, and add data and columns"""

    page_size = 10
    markdown_options = {"link_target": "_blank"}

    table = dash_table.DataTable(
        data=data,
        columns=columns,
        id="sso_lc_table",
        page_size=page_size,
        style_as_list_view=True,
        sort_action="native",
        filter_action="native",
        markdown_options=markdown_options,
        fixed_columns={"headers": True, "data": 1},
        style_data={"backgroundColor": "rgb(248, 248, 248, .7)"},
        style_table={"maxWidth": "100%"},
        style_cell={"padding": "5px", "textAlign": "center", "overflow": "hidden"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248, .7)"}
        ],
        style_header={"backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
    )
    return table


def display_table_results(table):

    return dbc.Container(
        [
            dcc.RadioItems(["Trajectory", "Orbit"], "Trajectory", id="sso-orb-radio"),
            table,
        ]
    )


@app.callback(
    [Output("sso_lc_table", "data"), Output("sso_lc_table", "columns")],
    [
        Input("sso-orb-radio", "value"),
        Input("pdf_orb", "data"),
        Input("pdf_lc", "data"),
    ],
    [State("sso_lc_table", "data"), State("sso_lc_table", "columns")],
)
def update_sso_table(orb_v_radio, json_orb, json_lc, data, columns):

    markdown_trajid = lambda traj_id: markdownify_objectid(
        traj_id, "trajid_{}".format(traj_id)
    )
    if orb_v_radio == "Orbit":
        pdf_orb = pd.read_json(json_orb).sort_values(["d:trajectory_id", "d:ref_epoch"])
        pdf_orb["d:trajectory_id"] = pdf_orb["d:trajectory_id"].apply(markdown_trajid)
        pdf_orb = pdf_orb.to_dict("records")

        colnames_to_display = [
            "d:trajectory_id",
            "d:ref_epoch",
            "d:a",
            "d:rms_a",
            "d:e",
            "d:rms_e",
            "d:i",
            "d:rms_i",
        ]

        columns = [
            {
                "id": c,
                "name": c,
                "type": "text",
                # 'hideable': True,
                "presentation": "markdown",
            }
            for c in colnames_to_display
        ]

        return pdf_orb, columns

    elif orb_v_radio == "Trajectory":
        original_pdf = pd.DataFrame.from_dict(data)
        if "d:jd" in original_pdf:
            raise PreventUpdate

        pdf_lc = pd.read_json(json_lc).sort_values(["d:trajectory_id", "d:jd"])
        pdf_lc["d:trajectory_id"] = pdf_lc["d:trajectory_id"].apply(markdown_trajid)
        pdf_lc = pdf_lc.to_dict("records")

        colnames_to_display = ["d:trajectory_id", "d:jd", "d:candid", "d:ra", "d:dec"]

        columns = [
            {
                "id": c,
                "name": c,
                "type": "text",
                # 'hideable': True,
                "presentation": "markdown",
            }
            for c in colnames_to_display
        ]

        return pdf_lc, columns

    else:
        raise PreventUpdate


@app.callback(
    Output("table_lc_res", "children"),
    [Input("pdf_lc", "data")],
)
def results(json_lc):

    pdf_lc = pd.read_json(json_lc).sort_values(["d:trajectory_id", "d:jd"])
    pdf_lc["d:trajectory_id"] = pdf_lc["d:trajectory_id"].apply(
        lambda traj_id: markdownify_objectid(traj_id, "trajid_{}".format(traj_id))
    )
    pdf_lc = pdf_lc.to_dict("records")
    colnames_to_display = ["d:trajectory_id", "d:jd", "d:candid", "d:ra", "d:dec"]

    columns = [
        {
            "id": c,
            "name": c,
            "type": "text",
            # 'hideable': True,
            "presentation": "markdown",
        }
        for c in colnames_to_display
    ]

    table = populate_sso_table(pdf_lc, columns)
    return dbc.Container([html.Br(), display_table_results(table)])


def construct_sso_stat_figure(pdf_orb, mpc_ae, xdata, ydata):

    xcand_data = pdf_orb["d:{}".format(xdata)].values
    ycand_data = pdf_orb["d:{}".format(ydata)].values

    is_distant = mpc_ae["Orbit_type"] == "Distant Object"

    no_distant = mpc_ae[~is_distant]
    distant = mpc_ae[is_distant]


    data = []
    for orb_type in mpc_ae["Orbit_type"].unique():
        tmp_df = no_distant[no_distant["Orbit_type"] == orb_type]
        x = tmp_df[xdata]
        y = tmp_df[ydata]
        data.append(go.Scattergl(
            x=x,
            y=y,
            mode='markers',
            name=orb_type,
            opacity=0.5
            # marker=dict(color=random_color()[2])
        ))

    data.append(
        go.Scattergl(
            x=distant[xdata],
            y=distant[ydata],
            mode='markers',
            name=distant["Orbit_type"].values[0],
            visible='legendonly',
            opacity=0.5,
            marker=dict(color='rgba(152, 0, 0, .5)')
        )
    )

    data.append(
        go.Scattergl(
            x=xcand_data,
            y=ycand_data,
            mode='markers',
            name="Fink SSO candidates",
            marker=dict(
                size=10,
                line=dict(
                    color='rgba(70, 138, 94, 0.5)',
                    width=2
                ),
                color='rgba(111, 235, 154, 0.5)'
            )
        )
    )

    custom_title = {
        "a" : "semi major axis (AU)",
        "e" : "eccentricity",
        "i" : "inclination (degree)"
    }

    layout_sso_ae = dict(
        margin=dict(l=50, r=30, b=0, t=0),
        hovermode="closest",
        hoverlabel={"align": "left"},
        legend=dict(
            font=dict(size=10),
            orientation="h",
            xanchor="right",
            x=1,
            y=1.2,
            bgcolor="rgba(218, 223, 225, 0.3)",
        ),
        yaxis={"title": custom_title[ydata], "automargin": True},
        xaxis={"title": custom_title[xdata], "automargin": True},
    )

    return {"data": data, "layout": layout_sso_ae}




@app.callback(Output("ae_distrib", "children"), [Input("pdf_orb", "data"), Input("mpc_data", "data")])
def construct_ae_distrib(json_orb, json_mpc):

    pdf_orb = pd.read_json(json_orb)
    mpc_ae = pd.read_json(json_mpc)

    fig = construct_sso_stat_figure(pdf_orb, mpc_ae, "a", "e")

    graph = dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        id="stats_sso"
    )
    card = dmc.Paper(graph, radius="xl", p="md", shadow="xl", withBorder=True)

    xaxis_drop = dcc.Dropdown(
        ["a", "e", "i"],
        id="xaxis_data"
    )

    yaxis_drop = dcc.Dropdown(
        ["a", "e", "i"],
        id="yaxis_data"
    )


    # add a time slider to filter the SSO trajectories by date in the a/e plot. 

    div = html.Div([
        card,
        xaxis_drop,
        yaxis_drop
    ])
    return div

@app.callback(
    Output("stats_sso", "figure"),
    [Input("xaxis_data", "value"), 
    Input("yaxis_data", "value"),
    Input("pdf_orb", "data"),
    Input("mpc_data", "data")]
)
def change_axis(xaxis_value, yaxis_value, json_orb, json_mpc):

    if xaxis_value != None and yaxis_value != None:
        app.logger.info(xaxis_value)
        app.logger.info(yaxis_value)

        pdf_orb = pd.read_json(json_orb)
        mpc_ae = pd.read_json(json_mpc)

        fig = construct_sso_stat_figure(pdf_orb, mpc_ae, xaxis_value, yaxis_value)

        return fig
    else:
        raise PreventUpdate



def layout(is_mobile):
    """ """

    if is_mobile:
        layout_ = html.Div(
            [
                html.Br(),
                html.Br(),
                dbc.Container(id="stat_row_mobile"),
                html.Br(),
                html.Div(id="object-stats", style={"display": "none"}),
            ],
            className="home",
            style={
                "background-image": "linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url(/assets/background.png)",
                "background-size": "contain",
            },
        )
    else:
        label_style = {"color": "#000"}
        tabs_ = dbc.Tabs(
            [
                dbc.Tab(
                    dbc.Container(id="table_lc_res"),
                    label="Solar System Candidate table",
                    label_style=label_style,
                ),
                dbc.Tab(
                    html.Div(id="ae_distrib"), # edit props 
                    label="a/e distribution",
                    label_style=label_style
                ),
            ]
        )

        layout_ = html.Div(
            [
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                dbc.Row(
                    [dbc.Col(tabs_)]
                ),
                dcc.Store(id="pdf_lc"),
                dcc.Store(id="pdf_orb"),
                dcc.Store(id="mpc_data")
            ],
            className="home",
            style={
                "background-image": "linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url(/assets/background.png)",
                "background-size": "contain"
            },
        )

    return layout_
