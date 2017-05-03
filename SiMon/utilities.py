"""
Utility class.
"""


class Utilities(object):

    @staticmethod
    def progress_bar(val, val_max, val_min=0, prefix='', suffix='', bar_len=30):
        """
        Displays a progress bar in the simulation tree.
        :param val:
        :param val_max:
        :param val_min:
        :param prefix:
        :param suffix:
        :param bar_len:
        :return:
        """
        if val_max == 0:
            return ''
        else:
            skipped_len = int(round(bar_len * val_min) / float(val_max))
            filled_len = int(round(bar_len * (val - val_min) / float(val_max)))
            # percents = round(100.0 * count / float(total), 1)
            bar = '.' * skipped_len + '|' * filled_len + '.' * (bar_len - filled_len - skipped_len)
            # return '[%s] %s%s %s\r' % (bar, percents, '%', suffix)
            return '%s [%s] %s\r' % (prefix, bar, suffix)

    @staticmethod
    def highlighted_text(text, color=None, bold=False):
        colors = ['red', 'blue', 'cyan', 'green', 'reset']
        color_codes = ['\033[31m', '\033[34m', '\033[36m', '\033[32m', '\033[0m']
        color_codes_bold = ['\033[1;31m', '\033[1;34m', '\033[1;36m', '\033[0;32m', '\033[0;0m']

        if color not in colors:
            color = 'reset'
        if bold is False:
            return '%s%s%s' % (color_codes[colors.index(color)], text, color_codes[colors.index('reset')])
        else:
            return '%s%s%s' % (color_codes_bold[colors.index(color)], text, color_codes_bold[colors.index('reset')])
