# Copyright 2021 AstroLab Software
# Author: Julien Peloton
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

dcc.Location(id='url', refresh=False)

def heatmap_content():
    """
    """
    layout_ = html.Div(
        [
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(id='heatmap_stat', width=8)
                ]
            ),
        ],
    )

    return layout_

def timelines():
    """
    """
    layout_ = html.Div(
        [
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(id='evolution', width=8)
                ]
            ),
        ],
    )

    return layout_

def layout(is_mobile):
    """
    """
    if is_mobile:
        tabs_ = None
    else:
        label_style = {"color": "#000"}
        tabs_ = dbc.Tabs(
            [
                dbc.Tab(heatmap_content(), label="Heatmap", tab_style={"margin-left": "auto"}, label_style=label_style),
                dbc.Tab(timelines(), label="Timelines", label_style=label_style),
                dbc.Tab(label="TNS", disabled=True),
            ]
        )

    if is_mobile:
        layout_ = None
    else:
        layout_ = html.Div(
            [
                html.Br(),
                html.Br(),
                dbc.Row(
                    [
                        html.Br(),
                        dbc.Col(tabs_, width=12)
                    ],
                    justify="around", no_gutters=True
                )
            ],
            className='home',
            style={
                'background-image': 'linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url(/assets/background.png)',
                'background-size': 'contain'
            }
        )

    return layout_
