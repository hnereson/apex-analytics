import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

class BasePlot():
    def __init__(self):
        self.font = 'monospace'

    def style_chart(self, chart, title_text, width=600, height=300, grid=True):
        if width == False and height ==False and grid == True:
             chart = chart.properties(
            title=alt.TitleParams(title_text, fontSize=16, font=self.font, anchor='middle')
        ).configure_axis(
            labelFont=self.font,
            titleFont=self.font
        ).configure_legend(
            labelFont=self.font,
            titleFont=self.font
        )
        elif grid==False:
            chart = chart.properties(
                width=width, 
                height=height, 
                title=alt.TitleParams(title_text, fontSize=16, font=self.font, anchor='middle')
            ).configure_view(
                strokeWidth=0  # Remove border
            ).configure_axis(
                labelFont=self.font,
                titleFont=self.font,
                grid=False,
                domain=False,  # Hide axis line
                ticks=False  # Hide axis ticks
            ).configure_legend(
                labelFont=self.font,
                titleFont=self.font
            )
        else:
            chart = chart.properties(
                width=width, 
                height=height, 
                title=alt.TitleParams(title_text, fontSize=16, font=self.font, anchor='middle')
            ).configure_axis(
                labelFont=self.font,
                titleFont=self.font
            ).configure_legend(
                labelFont=self.font,
                titleFont=self.font
            )
        return chart

    def plot_data_with_tooltip(self, data, x_field, y_field, color_field, hex_palette, x_scale, y_scale):
        nearest = alt.selection_point(nearest=True, on='mouseover', fields=[x_field], empty=False)

        line = alt.Chart(data).mark_line(interpolate='basis').encode(
            x=alt.X(f'{x_field}:Q', scale=alt.Scale(domain=x_scale), title=None),
            y=alt.Y(f'{y_field}:Q', scale=alt.Scale(domain=y_scale), title=None),
            color=alt.Color(f'{color_field}:N', scale=alt.Scale(range=hex_palette))
        )

        selectors = alt.Chart(data).mark_point().encode(
            x=f'{x_field}:Q',
            opacity=alt.value(0),
        ).add_params(
            nearest
        )

        points = line.mark_point().encode(
            opacity=alt.condition(nearest, alt.value(1), alt.value(0))
        )

        text = line.mark_text(align='left', dx=5, dy=-5).encode(
           text=alt.condition(nearest, f'{y_field}:Q', alt.value(' '))
        )

        rules = alt.Chart(data).mark_rule(color='gray').encode(
            x=f'{x_field}:Q',
        ).transform_filter(
            nearest
        )

        return alt.layer(line, selectors, points, rules, text)

class HeatmapPlot(BasePlot):
    def __init__(self):
        super().__init__()
    
    def prepare_heatmap_data(self, heatmap_data):
        # Reset index for the heatmap data
        data = heatmap_data.reset_index().melt(id_vars='year', value_name='% moved out', var_name='month')
        return data
    
    def plot_altair_heatmap(self, data, x_field, y_field, color_field, title_text, color_palette="teals"):
        """
        Create a heatmap using Altair based on the provided data.

        Parameters:
        - data (pd.DataFrame): Data for the heatmap.
        - x_field (str): Field to be used for the x-axis.
        - y_field (str): Field to be used for the y-axis.
        - color_field (str): Field to determine the color of the heatmap cells.
        - title_text (str): Title for the heatmap.
        - color_scheme (str, optional): Color scheme for the heatmap. Defaults to 'teals'.

        Returns:
        - chart: Altair heatmap chart.
        """
        # Define the heatmap chart
        chart = alt.Chart(data).mark_rect().encode(
            x=alt.X(f'{x_field}:O', title=''),
            y=alt.Y(f'{y_field}:O', title=''),
            color=alt.Color(f'{color_field}:Q', scale=alt.Scale(scheme=color_palette)),
            tooltip=[x_field, y_field, color_field]
        )

        # Style the chart
        styled_chart = self.style_chart(chart, title_text, width=600, height=400)
        return styled_chart

    def display_heatmap(self, data, x_field, y_field, color_field, title_text):
        """
        Display the heatmap using Streamlit.

        Parameters:
        - data (pd.DataFrame): Data for the heatmap.
        - x_field (str): Field to be used for the x-axis.
        - y_field (str): Field to be used for the y-axis.
        - color_field (str): Field to determine the color of the heatmap cells.
        - title_text (str): Title for the heatmap.
        """
        # Create a palette that starts from a light teal (close to white) and progresses to a dark teal

        # data = self.prepare_heatmap_data(data)
        heatmap = self.plot_altair_heatmap(data, x_field, y_field, color_field, title_text)
        st.altair_chart(heatmap, use_container_width=True)

class HistogramPlot(BasePlot):
    def __init__(self):
        super().__init__()
    
    def prepare_histogram_data(self, move_out_df, start_date, end_date):
        """
        Prepare data for the histogram based on the provided date range.
        
        Parameters:
        - move_out_df (pd.DataFrame): DataFrame with move-out data.
        - start_date (datetime): Start date for the desired range.
        - end_date (datetime): End date for the desired range.
        
        Returns:
        - sorted_df (pd.DataFrame): DataFrame with Y/Y change prepared for histogram plotting.
        """
        move_out_df['date'] = move_out_df['date'].dt.date

        # Now filter based on the date range
        current_year_data = move_out_df[(move_out_df['date'] >= start_date) & (move_out_df['date'] <= end_date)]
        previous_year_data = move_out_df[(move_out_df['date'] >= (start_date - pd.DateOffset(years=1)).date()) & (move_out_df['date'] <= (end_date - pd.DateOffset(years=1)).date())]

        # Merge the two dataframes on 'site_code' to calculate the Y/Y change
        merged_df = current_year_data[['site_code', '% moved out']].merge(previous_year_data[['site_code', '% moved out']], on='site_code', suffixes=('_current', '_prev'))

        # Calculate the Y/Y change
        merged_df['yoy_change'] = merged_df['% moved out_current'] - merged_df['% moved out_prev']

        merged_df = merged_df[~merged_df['yoy_change'].isna()]
        # Sort the dataframe by 'yoy_change'
        sorted_df = merged_df.sort_values(by='yoy_change', ascending=False)

        return sorted_df

    def plot_altair_histogram(self, data, x_field, title_text, x_title, y_title, bar_color="teal", num_bins=30, bar_width=15, density=False):
        """
        Create a histogram using Altair based on the provided data.
        
        Parameters:
        - data (pd.DataFrame): Data for the histogram.
        - x_field (str): Field to be used for the x-axis.
        - title_text (str): Title for the histogram.
        - color_palette (str, optional): Color palette for the histogram. Defaults to None.
        
        Returns:
        - chart: Altair histogram chart.
        """
        min_value = data[x_field].min()
        max_value = data[x_field].max()
        bin_edges = np.linspace(min_value, max_value, num_bins + 1)

        # Assign each data point to a bin
        data['bin'] = np.digitize(data[x_field], bin_edges, right=True) - 1

        # Group by the bin and count the number of data points in each bin
        binned_data = data.groupby('bin').size().reset_index(name='count')
        binned_data[x_field] = (bin_edges[binned_data['bin']] + bin_edges[binned_data['bin']]) / 2

        # Plot the histogram using Altair
        chart = alt.Chart(binned_data).mark_bar(color=bar_color, size=bar_width).encode(
            x=alt.X(f'{x_field}:Q', title=x_title, axis=alt.Axis(grid=False)),
            y=alt.Y('count:Q', title=y_title, axis=alt.Axis(grid=False)),
            tooltip=[x_field, 'count']
        )
        # Density plot (like KDE)
        max_count = binned_data['count'].max()
        if density == True:
            density = alt.Chart(data).transform_density(
                density=x_field,
                as_=[x_field, 'density'],
                bandwidth=0.5  # Adjust bandwidth as needed
            ).transform_calculate(
                scaled_density=f'datum.density * {max_count}'  # Rescale density values
            ).mark_line(color='red').encode(
                x=f'{x_field}:Q',
                y=alt.Y('scaled_density:Q', axis=alt.Axis(grid=False))
            )

            chart = (chart + density)
        
        chart = chart.interactive()
        # Style the chart
        styled_chart = self.style_chart(chart, title_text, width=600, height=400)
        st.altair_chart(styled_chart, use_container_width=True)


class ScatterPlot(BasePlot):
    def __init__(self):
        super().__init__()

    def prepare_scatter_data(self, data, pred_moveouts_df, end_date):
        """
        Prepare data for the scatterplot based on the provided end date.
        
        Parameters:
        - move_out_df (pd.DataFrame): DataFrame with move-out data.
        - pred_moveouts_df (pd.DataFrame): DataFrame with predicted move-outs.
        - end_date (datetime): End date for the desired range.
        
        Returns:
        - merged_scatter_data (pd.DataFrame): DataFrame prepared for scatter plotting.
        """
        
        # Filter move_out_df for the given end_date
        filtered_data = data[data['date'] == end_date]

        # Merge the filtered data with predicted move-outs
        merged_scatter_data = filtered_data[['site_code', '% moved out', 'move_outs']].merge(pred_moveouts_df, on='site_code')
        merged_scatter_data['percentage_difference'] = 100 * (merged_scatter_data['move_outs'] - merged_scatter_data['predicted_moveouts']) / merged_scatter_data['predicted_moveouts']

        return merged_scatter_data

    def plot_altair_scatterplot(self, data, x_field, y_field, title_text, color_palette="teals"):
        """
        Create a scatterplot using Altair based on the provided data.
        
        Parameters:
        - data (pd.DataFrame): Data for the scatterplot.
        - x_field (str): Field to be used for the x-axis.
        - y_field (str): Field to be used for the y-axis.
        - title_text (str): Title for the scatterplot.
        - color_palette (str, optional): Color palette for the scatterplot. Defaults to None.
        
        Returns:
        - chart: Altair scatterplot chart.
        """
        # Define the scatterplot chart
        chart = alt.Chart(data).mark_circle().encode(
            x=alt.X(f'{x_field}:Q', title='% Moved Out (Sep 2023)'),
            y=alt.Y(f'{y_field}:Q', title='% Difference (Actual - Pred) / Pred'),
            color=alt.Color(scale=alt.Scale(scheme=color_palette)),
            tooltip=[x_field, y_field]
        )

        # Style the chart
        styled_chart = self.style_chart(chart, title_text, width=600, height=400)
        st.altair_chart(styled_chart, use_container_width=True)
    
    def plot_projects_scatterplot(self, x_axis, y_axis, data, title_text, order):
        chart = alt.Chart(data).mark_circle().encode(
            x=alt.X(f'{x_axis}:Q', title='Days Open'),
            y=alt.Y(f'{y_axis}:N', title=None, sort=order),
            size='count:Q',
            color=alt.Color(f'{y_axis}:N', legend=alt.Legend(title="Status Group")),
            tooltip=[f'{y_axis}:N', f'{x_axis}:Q', 'count:Q']
        )

        # Style the chart
        styled_chart = self.style_chart(chart, title_text, width=600, height=400)
        st.altair_chart(styled_chart, use_container_width=True)


class BarPlot(BasePlot):
    def __init__(self):
        super().__init__()
        # x = year , y=move outs
    def plot_altair_monthly_bars(self, data, x_field, y_field, secondary_x, title_text, color_palette="teals"):
        # Sum the data by month and year
        summed_data = data.groupby(['month', 'year'])[y_field].sum().reset_index()

        # Define the bar chart
        chart = alt.Chart(summed_data).mark_bar().encode(
            x=alt.X(f'{x_field}:O', title=None, axis=alt.Axis(labels=False, ticks=False, domain=False)),  # Hide x-axis labels, ticks, and domain),
            y=alt.Y(f'{y_field}:Q', title=None),
            color=alt.Color(f'{x_field}:O', scale=alt.Scale(scheme=color_palette), legend=alt.Legend(orient='right')),
            tooltip=[x_field, secondary_x, y_field]
        ).facet(
            column=alt.Column(f'{secondary_x}', title=None, header=alt.Header(labelOrient="bottom", labelPadding=10))  # Adjust label position and padding for month
        )
        styled_chart = self.style_chart(chart, title_text, width=False, height=False)
        styled_chart= styled_chart.configure_view(stroke=None).configure_axis(grid=False)
        st.altair_chart(styled_chart, use_container_width=True)
    
class Boxplot(BasePlot):
    def __init__(self):
        super().__init__()

    def prepare_boxplot_data(self, data, value_field, category_field):
        # Boxplot data preparation code
        prepared_data = data[[value_field, category_field]]
        return prepared_data

    def plot_altair_boxplot(self, data, value_field, category_field, title_text, color_scheme):
        """
        Create a boxplot using Altair based on the provided data.

        Parameters:
        - data (pd.DataFrame): Data for the boxplot.
        - value_field (str): Field to be used for the boxplot value.
        - category_field (str): Field to be used for the boxplot category.
        - title_text (str): Title for the boxplot.
        - color_scheme (str): The color scheme for the boxplot.

        Returns:
        - chart: Altair boxplot chart.
        """
        # Define the boxplot chart with the extent to 1.5 for excluding extreme outliers
        chart = alt.Chart(data).mark_boxplot(extent=1.5, size=40).encode(  # Adjusted the 'size' here
            x=alt.X(f'{category_field}:N', title='', axis=alt.Axis(labelAngle=0)),  # Optional: Adjust label angle for readability
            y=alt.Y(f'{value_field}:Q', title=''),
            color=alt.Color(f'{category_field}:N', scale=alt.Scale(scheme=color_scheme)),
            tooltip=[category_field, value_field]
        ).properties(
            width=600  # Adjusted the width of the chart. You can also use 'step' with a band scale for the x-axis to control box width.
        ).interactive()

        # Style the chart
        styled_chart = self.style_chart(chart, title_text)
        return styled_chart

    def display_boxplot(self, data, value_field, category_field, title_text, color_scheme='blues'):
        """
        Display the boxplot using Streamlit.

        Parameters:
        - data (pd.DataFrame): Data for the boxplot.
        - value_field (str): Field to be used for the boxplot value.
        - category_field (str): Field to be used for the boxplot category.
        - title_text (str): Title for the boxplot.
        - color_scheme (str): The color scheme for the boxplot.
        """
        prepared_data = self.prepare_boxplot_data(data, value_field, category_field)
        boxplot = self.plot_altair_boxplot(prepared_data, value_field, category_field, title_text, color_scheme)
        st.altair_chart(boxplot, use_container_width=True)

