import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class CV():
    def __init__(self, metadata, svgplot):
        """
        metadata: dict
        """
        self.svgplot = svgplot
        self.metadata = metadata
        self.svgplot.create_df()

        # TODO: These labels should either be extracted from the svg or yaml file
        self.xlabel = 'U'

        # TODO: should be j if both current and normalized to are given in the yaml file
        self.ylabel = 'I'

        # TODO: All the rest in the init is presumably not necessary
        self.description = self.metadata['figure description']

        self.xunit = self.description['potential scale']['unit']

        self.yunit = self.description['current']['unit']

        self.get_rate()

        self.modify_df()

    def get_rate(self):  # TODO: probably not required
        r'''
        Return rate based on the x coordinate units.

        At the moment we simply use the value.
        '''
        self.rate = self.description['scan rate']['value']
        return self.rate

    def modify_df(self):
        # Create potential columns
        self.df = self.create_df_U_axis(self.svgplot.dfs[0])
        # Create current columns
        self.df = pd.concat(
            [self.df, self.create_df_I_axis(self.svgplot.dfs[0])],
            axis=1)

        # create time axis
        self.df['t'] = self.create_df_time_axis(self.svgplot.dfs[0])

    def create_df_U_axis(self, df):
        r'''
        Create voltage axis in the dataframe based on the units given in the
        figure description.
        '''
        df_ = df.copy()
        # Call a dict and remove the if functions
        if self.xunit == 'V':
            df_['U_V'] = df['U']

        if self.xunit == 'mV':
            df_['U_V'] = df['U']/1E3

        df_['U_mV'] = df_['U_V']*1E3

        return df_[['U_V', 'U_mV']]

    def create_df_I_axis(self, df):
        r'''
        Create current or current density axis in the dataframe based on the
        units given in the figure description.
        '''
        df_ = df.copy()
        if self.yunit == 'A':
            df_['I_A'] = df['I']

        if self.yunit == 'mA':
            df_['I_A'] = df['I']/1E3

        if self.yunit == 'uA':
            df_['I_A'] = df['I']/1E6

        df_['I_mA'] = df_['I_A']*1E3
        df_['I_uA'] = df_['I_A']*1E6

        return df_[['I_A', 'I_mA', 'I_uA']]

    def create_df_time_axis(self, df):
        r'''
        Create a time axis in the dataframe based on the scan rate given in the
        figure description.
        '''
        df_ = df.copy()
        df_['deltaU'] = abs(df_[self.xlabel].diff())
        df_['cumdeltaU'] = df_['deltaU'].cumsum()
        df_['t'] = df_['cumdeltaU']/self.get_rate()
        return df_['t']

    def plot_cv(self):
        self.df.plot(x='U_V', y='I_uA')
        plt.xlabel(f'{self.xlabel} / {self.xunit}')
        plt.ylabel(f'{self.ylabel} / {self.yunit}')

    def create_csv(self, filename):
        csvfile = Path(filename).with_suffix('.csv')
        self.df.to_csv(csvfile, index=False)
