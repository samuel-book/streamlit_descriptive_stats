"""
Streamlit app template.

Because a long app quickly gets out of hand,
try to keep this document to mostly direct calls to streamlit to write
or display stuff. Use functions in other files to create and
organise the stuff to be shown. In this example, most of the work is
done in functions stored in files named container_(something).py
"""
# ----- Imports -----
import streamlit as st
import pandas as pd
import numpy as np
import geojson
import plotly.graph_objs as go


# Add an extra bit to the path if we need to.
# Try importing something as though we're running this from the same
# directory as the landing page.
try:
    from utilities_descriptive.fixed_params import page_setup
except ModuleNotFoundError:
    # If the import fails, add the landing page directory to path.
    # Assume that the script is being run from the directory above
    # the landing page directory, which is called
    # streamlit_lifetime_stroke.
    import sys
    sys.path.append('./streamlit_descriptive_stats/')
    # The following should work now:
    from utilities_descriptive.fixed_params import page_setup
try:
    test_file = pd.read_csv(
        './data_descriptive/stroke_teams.csv',
        index_col='stroke_team'
        )
    dir = './'
except FileNotFoundError:
    # If the import fails, add the landing page directory to path.
    # Assume that the script is being run from the directory above
    # the landing page directory, which is called
    # stroke_outcome_app.
    dir = 'streamlit_descriptive_stats/'

# Custom functions:
# from utilities_descriptive.fixed_params import page_setup
# from utilities.inputs import \
#     write_text_from_file
# Containers:
# import utilities.container_inputs
# import utilities.container_results
# import utilities.container_details


def build_lists_for_each_team_and_year(
        stroke_team_list,
        year_options,
        region_team_list
        ):
    """
    Builds a list containing:
    Team 1 (2016 to 2021)
    Team 1 (2016)
    Team 1 (2017)
    ...
    Team 1 (2021)
    Team 2 (2016 to 2021)
    Team 2 (2016)
    Team 2 (2017)
    ...
    Team 2 (2021)
    """
    stroke_team_list_years = [
        f'{s} ({y})'
        for s in ['all E+W'] + stroke_team_list
        for y in year_options
    ]

    # Similar for regions:
    region_team_list_years = [
        region
        for region in ['all E+W'] + region_team_list
        for y in year_options
    ]
    return stroke_team_list_years, region_team_list_years


def inputs_region_choice(df_stroke_team, containers=[]):
    # List of regions
    region_list = sorted(list(set(
        df_stroke_team['RGN11NM'].squeeze().values
        )))

    regions_selected_bool = []
    for r, region in enumerate(region_list):
        with containers[r % len(containers)]:
            region_bool = st.checkbox(region, key=region)
        regions_selected_bool.append(region_bool)
    regions_selected = list(np.array(region_list)[regions_selected_bool])
    return regions_selected


def input_stroke_teams_to_highlight(
        df_stroke_team,
        regions_selected,
        all_teams_str,
        year_options,
        all_years_str='',
        containers=[]
        ):
    """
    One input per year
    """
    if len(containers) < 1:
        containers = st.columns(4)

    stroke_team_list = (
        reduce_big_lists_to_regions_selected(
            df_stroke_team,
            regions_selected,
            ))
    # Add on the "all teams" team:
    stroke_team_list = [all_teams_str] + list(
        stroke_team_list)

    all_stroke_teams_selected = []
    for y, year in enumerate(year_options):
        # Use the format function in the multiselect to change how
        # the team names are displayed without changing their names
        # in the underlying data.
        # Because the current ordering of the list is by team and then
        # by year, this also visually breaks up the list into groups of
        # each team.
        with containers[y % len(containers)]:
            stroke_teams_selected = st.multiselect(
                f'{year}',
                options=stroke_team_list,
                default='all E+W' if year == all_years_str else None,
                key=f'input_teams_{year}'
                )
        stroke_teams_selected = [
            f'{t} ({year})' for t in stroke_teams_selected]
        all_stroke_teams_selected += stroke_teams_selected

    return all_stroke_teams_selected


def reduce_big_lists_to_regions_selected(
        df_stroke_team,
        regions_selected,
    ):

    # Create a shorter list of teams.
    # This contains only teams in the selected region(s).
    # List of stroke teams
    stroke_team_list = list(df_stroke_team['Stroke Team'].squeeze().values)
    # List of regions
    region_team_list = list(df_stroke_team['RGN11NM'].squeeze().values)

    full_list_regions_selected_bool = np.full(
        len(region_team_list), False)
    for region in ['all E+W'] + regions_selected:
        inds = np.where(np.array(region_team_list) == region)
        full_list_regions_selected_bool[inds] = True

    stroke_team_list_years_by_region_selected = (
        np.array(stroke_team_list)[full_list_regions_selected_bool]
    )
    return stroke_team_list_years_by_region_selected


def plot_geography_pins(df_stroke_team):
    # Import geojson data:
    geojson_file = 'regions_EW.geojson'
    with open(dir + './data_descriptive/region_geojson/' + geojson_file) as f:
        geojson_ew = geojson.load(f)

    # Find extent of this geojson data.
    coords = np.array(list(geojson.utils.coords(geojson_ew)))
    extent = [
        coords[:, 0].min(),
        coords[:, 0].max(),
        coords[:, 1].min(),
        coords[:, 1].max()
    ]

    # Get the names of the regions out of the geojson:
    region_list = []
    for feature in geojson_ew['features']:
        region = feature['properties']['RGN11NM']
        region_list.append(region)

    # Create a dummy dataframe of region names and some value for colours.
    df_regions = pd.DataFrame(region_list, columns=['RGN11NM'])
    df_regions['v'] = [0] * len(df_regions)  # Same value, same colour.

    # Plot:
    fig = go.Figure()
    fig.update_layout(
        width=500,
        height=500,
        margin_l=0, margin_r=0, margin_t=0, margin_b=0
        )

    # Add region polygons:
    fig.add_trace(go.Choropleth(
        geojson=geojson_ew,
        locations=df_regions['RGN11NM'],
        z=df_regions['v'],
        featureidkey='properties.RGN11NM',
        colorscale='Picnic',
        showscale=False,
        hoverinfo='skip'
    ))
    # Add scatter markers for all hospitals:
    fig.add_trace(go.Scattergeo(
        lon=df_stroke_team['long'],
        lat=df_stroke_team['lat'],
        customdata=np.stack([df_stroke_team['Stroke Team']], axis=-1),
        mode='markers',
        # marker_color=df_stroke_team['RGN11NM']
    ))

    # Update geojson projection.
    # Projection options:
    #   august  eckert1  fahey  times  van der grinten
    fig.update_layout(
        geo_scope='europe',
        geo_projection=go.layout.geo.Projection(type='times'),
        geo_lonaxis_range=[extent[0], extent[1]],
        geo_lataxis_range=[extent[2], extent[3]],
        # geo_resolution=50,
        geo_visible=False
    )
    fig.update_geos(fitbounds="locations", visible=False)

    # Update hover info for scatter points:
    fig.update_traces(
        hovertemplate='%{customdata[0]}<extra></extra>',
        selector=dict(type='scattergeo')
    )

    plotly_config = {
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    }
    st.plotly_chart(fig, config=plotly_config)
    st.caption('Locations of the stroke teams, colour-coded by region.')


def plot_violins(
        summary_stats_df,
        feature,
        year_options,
        stroke_teams_selected_without_year,
        all_years_str,
        all_teams_str
        ):
    fig = go.Figure()

    fig.update_layout(
        width=1300,
        height=500,
        # margin_l=0, margin_r=0, margin_t=0, margin_b=0
        )

    # Rename to keep code short:
    s = summary_stats_df.T
    # Remove "all teams" data:
    s = s[s['stroke_team'] != 'all E+W']

    for y, year in enumerate(year_options):
        if year == all_years_str:
            colour = 'Thistle'
        else:
            colour = 'Grey'

        # Include "to numeric" in case some of the numbers
        # are secretly strings (despite my best efforts).
        violin_vals = pd.to_numeric(s[feature][s['year'] == year])

        fig.add_trace(go.Violin(
            x=s['year'][s['year'] == year],
            y=violin_vals,
            name=year,
            line=dict(color=colour),
            points=False,
            hoveron='points',
            showlegend=False
            ))

        # Add three scatter markers for min/max/median
        # with vertical line connecting them:
        fig.add_trace(go.Scatter(
            x=[year]*3,
            y=[violin_vals.min(), violin_vals.max(), violin_vals.median()],
            line_color='black',
            marker=dict(size=20, symbol='line-ew-open'),
            # name='Final Probability',
            showlegend=False,
            hoverinfo='skip',
            ))

    for stroke_team in stroke_teams_selected_without_year:
        if stroke_team != all_teams_str:
            scatter_vals = s[(
                # (s['year'] == year) &
                (s['stroke_team'] == stroke_team)
                )]
            fig.add_trace(go.Scatter(
                x=scatter_vals['year'],
                y=scatter_vals[feature],
                mode='markers',
                name=stroke_team
            ))

    fig.update_layout(yaxis_title=feature)
    # Move legend to bottom
    fig.update_layout(legend=dict(
        orientation='h',
        yanchor='top',
        y=-0.2,
        xanchor='right',
        x=0.9,
        # itemwidth=50
    ))

    plotly_config = {
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    }
    st.plotly_chart(fig, config=plotly_config)


def check_teams_in_stats_df(
        summary_stats_df,
        stroke_teams_selected,
        container_warnings
        ):
    """
    Check that all of the requested data exists.
    Remove any that aren't ok
    """
    try:
        # Smaller dataframe of only selected teams:
        df_to_show = summary_stats_df[stroke_teams_selected]
    except KeyError:
        # Remove teams that aren't in the dataframe.
        # Keep the valid ones in here:
        reduced_teams_to_show = []
        # Keep the invalid ones in here:
        missing_teams = []
        # Set up for printing a nice warning message:
        show_warning = False
        warning_str = 'There is no data for '

        # Sort the teams into the valid and invalid lists:
        for team in stroke_teams_selected:
            try:
                summary_stats_df[team]
                reduced_teams_to_show.append(team)
            except KeyError:
                show_warning = True
                missing_teams.append(team)

        # The dataframe containing only the valid teams:
        df_to_show = summary_stats_df[reduced_teams_to_show]

        # If there were missing teams (should always be True),
        # show the message.
        if show_warning is True:
            # Create a warning message to print.
            # e.g. "There is no data for {1}, {2} or {3}."
            warning_str = (
                warning_str +
                ', '.join(missing_teams[:-1])
                )
            if len(missing_teams) > 1:
                warning_str += ' or '
            warning_str = (
                warning_str + missing_teams[-1] + '.'
            )
            # Display the warning:
            with container_warnings:
                st.warning(warning_str, icon='⚠️')

    return df_to_show


def main():
    # ###########################
    # ##### START OF SCRIPT #####
    # ###########################
    page_setup()

    # Title:
    st.markdown('# 📊 Descriptive statistics')

    # Build up the page layout:
    _ = """
    +-----------------------------------------------------------------+
    | 📊 Descriptive statistics                                       |
    | <---------cols_inputs_map[0]---------><---cols_inputs_map[1]--->|
    |                                      |                          |
    |       container_input_regions        |                          |
    |                                      |      container_map       |
    |        container_input_teams         |                          |
    +--------------------------------------+--------------------------+
    |                   container_input_4hr_toggle                    |
    +-----------------------------------------------------------------+
    |                        container_results                        |
    +-----------------------------------------------------------------+
    |                        container_violins                        |
    +-----------------------------------------------------------------+
    """

    cols_inputs_map = st.columns([0.6, 0.4])
    with cols_inputs_map[0]:
        container_input_regions = st.container()
    with cols_inputs_map[0]:
        container_input_teams = st.container()
    with cols_inputs_map[1]:
        container_map = st.container()

    container_warnings = st.container()
    container_input_4hr_toggle = st.container()
    container_results_table = st.container()
    container_violins = st.container()

    # Each team input box:
    with container_input_teams:
        cols_t = st.columns(3)
        with cols_t[0]:
            st.markdown('All years:')
        with cols_t[1]:
            st.markdown('Separate years:')
        for col in cols_t[2:]:
            with col:
                # Unicode looks-like-a-space character
                # for vertical alignment with the other columns
                # that have text in.
                st.markdown('\U0000200B')
        containers_list_team_inputs = [
            cols_t[0],             # All years
            cols_t[1], cols_t[2],  # 2016, 2017
            cols_t[1], cols_t[2],  # 2018, 2019
            cols_t[1], cols_t[2]   # 2020, 2021
        ]

    with container_input_regions:
        containers_list_region_inputs = st.columns(3)

    # ###########################
    # ########## SETUP ##########
    # ###########################

    all_teams_str = 'all E+W'

    # Decide which descriptive stats file to use:
    with container_input_4hr_toggle:
        limit_to_4hr = st.toggle('Limit to arrival within 4hr')
    if limit_to_4hr:
        summary_stats_file = 'summary_stats_4hr.csv'
    else:
        summary_stats_file = 'summary_stats.csv'
    # Read in the data:
    summary_stats_df = pd.read_csv(
        f'{dir}/data_descriptive/{summary_stats_file}',
        index_col=0
        )

    # Import list of all stroke teams:
    df_stroke_team = pd.read_csv(
        f'{dir}/data_descriptive/hospitals_and_lsoas_descriptive_stats.csv',
        index_col=False
        ).sort_values('Stroke Team')

    with container_map:
        # Plot the team locations
        plot_geography_pins(df_stroke_team)

    # List of years in the data:
    year_options = sorted(set(summary_stats_df.loc['year']))
    # Move the "all years" option to the front of the list:
    all_years_str = '2016 to 2021'
    year_options.remove(all_years_str)
    year_options = [all_years_str] + year_options

    with container_input_regions:
        # Select regions:
        st.markdown('Show teams from these regions:')
        regions_selected = inputs_region_choice(
            df_stroke_team,
            containers_list_region_inputs
            )

    with container_input_teams:
        # Select stroke teams:
        stroke_teams_selected = input_stroke_teams_to_highlight(
            df_stroke_team,
            regions_selected,
            all_teams_str,
            year_options,
            all_years_str=all_years_str,
            containers=containers_list_team_inputs
            )

    # ###########################
    # ######### RESULTS #########
    # ###########################

    # Check that all of the requested data exists.
    # Remove any teams that don't exist and print a warning message.
    df_to_show = check_teams_in_stats_df(
        summary_stats_df,
        stroke_teams_selected,
        container_warnings
    )

    # Update the order of the rows to this:
    row_order = [
        'count',
        'age',
        'male',
        'infarction',
        'stroke severity',
        'onset-to-arrival time',
        'onset known',
        'arrive in 4  hours',
        'precise onset known',
        'onset during sleep',
        'use of AF anticoagulants',
        'prior disability',
        'prestroke mrs 0-2',
        'arrival-to-scan time',
        'thrombolysis',
        'scan-to-thrombolysis time',
        'death',
        'discharge disability',
        'increased disability due to stroke',
        'mrs 5-6',
        'mrs 0-2'
    ]
    df_to_show = df_to_show.loc[row_order]

    with container_results_table:
        st.header('Results')
        st.table(df_to_show)

    # #########################
    # ######### PLOTS #########
    # #########################

    with container_violins:
        st.header('Feature breakdown')

        feature = st.selectbox(
            'Pick a feature to plot',
            options=row_order,
            # default='count'
        )

        # Remove the (year) string from the selected teams:
        stroke_teams_selected_without_year = [
            team.split(' (')[0] for team in stroke_teams_selected]

        plot_violins(
            summary_stats_df,
            feature,
            year_options,
            stroke_teams_selected_without_year,
            all_years_str,
            all_teams_str
            )

    # ----- The end! -----


if __name__ == '__main__':
    main()
