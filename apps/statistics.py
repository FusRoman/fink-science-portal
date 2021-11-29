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

dcc.Location(id='url', refresh=False)

def layout(is_mobile):
    """
    """
    graph_evolution = dcc.Graph(
        style={
            'width': '100%',
            'height': '4pc'
        },
        config={'displayModeBar': False},
        id='evolution'
    )

    if is_mobile:
        layout_ = None
    else:
        layout_ = html.Div(
            [
                dbc.Row(
                    dbc.Col(dbc.Card(""), size=4),
                    dbc.Col(graph_evolution, size=8)
                )
            ],
            className='home',
            style={
                'background-image': 'linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url(/assets/background.png)',
                'background-size': 'contain'
            }
        )

    return layout_
