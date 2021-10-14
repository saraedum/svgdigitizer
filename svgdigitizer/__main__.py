# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021 Albert Engstfeld
#        Copyright (C) 2021 Johannes Hermann
#        Copyright (C) 2021 Julian Rüth
#        Copyright (C) 2021 Nicolas Hörmann
#
#  svgdigitizer is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  svgdigitizer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with svgdigitizer. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************
import click
import os.path

help_sampling = 'sampling interval on the x-axis'


@click.group()
def cli(): pass


@click.command()
@click.option('--sampling_interval', type=float, default=None, help=help_sampling)
@click.argument('svg', type=click.Path(exists=True))
def plot(svg, sampling_interval):
    from svgdigitizer.svgplot import SVGPlot
    from svgdigitizer.svg import SVG
    SVGPlot(SVG(open(svg, 'rb')), sampling_interval=sampling_interval).plot()


@click.command()
@click.option('--sampling_interval', type=float, default=None, help=help_sampling)
@click.option('--outdir', type=click.Path(file_okay=False), default=".", help='write output files to this directory')
@click.argument('svg', type=click.Path(exists=True))
def digitize(svg, sampling_interval):
    from svgdigitizer.svgplot import SVGPlot
    from svgdigitizer.svg import SVG
    plot = SVGPlot(SVG(open(svg, 'rb')), sampling_interval=sampling_interval)
    from pathlib import Path
    plot.df.to_csv(os.path.join(outdir, Path(svg).with_suffix('.csv').name), index=False)


@click.command()
@click.option('--sampling_interval', type=float, default=None, help='sampling interval on the x-axis in volt (V)')
@click.option('--metadata', type=click.File("rb"), default=None, help='yaml file with metadata')
@click.option('--package', is_flag=True, help='create .json in data package format')
@click.option('--outdir', type=click.Path(file_okay=False), default=".", help='write output files to this directory')
@click.argument('svg', type=click.Path(exists=True))
def cv(svg, sampling_interval, metadata, package, outdir):
    import yaml
    from astropy import units as u
    from svgdigitizer.svgplot import SVGPlot
    from svgdigitizer.svg import SVG
    from svgdigitizer.electrochemistry.cv import CV

    import os
    os.makedirs(str(outdir), exist_ok=True)

    # Determine unit of the voltage scale.
    cv = CV(SVGPlot(SVG(open(svg, 'rb'))))
    xunit = CV.get_axis_unit(cv.x_label.unit)
    if not xunit == u.V:
        # Determine conversion factor to volts.
        sampling_correction = xunit.to(u.V)
        sampling_interval = sampling_interval / sampling_correction

    if metadata:
        metadata = yaml.load(metadata, Loader=yaml.SafeLoader)

    cv = CV(SVGPlot(SVG(open(svg, 'rb')), sampling_interval=sampling_interval), metadata=metadata)

    from pathlib import Path
    csvname = Path(svg).with_suffix('.csv').name

    cv.df.to_csv(os.path.join(outdir, csvname), index=False)

    if package:
        from datapackage import Package
        p = Package(cv.metadata, base_path=outdir)
        p.infer(csvname)

    from datetime import datetime, date

    def defaultconverter(o):
        if isinstance(o, (datetime, date)):
            return o.__str__()

    import json
    with open(os.path.join(outdir, Path(svg).with_suffix('.json').name), "w") as outfile:
        json.dump(p.descriptor if package else cv.metadata, outfile, default=defaultconverter)


@click.command()
@click.option('--onlypng', is_flag=True, help='Only produce png files')
@click.argument('pdf')
def paginate(onlypng, pdf):
    from pdf2image import convert_from_path
    import svgwrite
    from svgwrite.extensions.inkscape import Inkscape
    from PIL import Image
    basename = pdf.split('.')[0]
    pages = convert_from_path(pdf, dpi=600)
    for idx, page in enumerate(pages):
        base_image_path = f'{basename}_p{idx}'
        page.save(f'{base_image_path}.png', 'PNG')
        if not onlypng:
            image = Image.open(f'{base_image_path}.png')
            width, height = image.size
            dwg = svgwrite.Drawing(f'{base_image_path}.svg', size=(f'{width}px', f'{height}px'), profile='full')
            Inkscape(dwg)
            img = dwg.add(svgwrite.image.Image(f'{base_image_path}.png', insert=(0, 0), size=(f'{width}px', f'{height}px')))

            # workaround: add missing locking attribute for image element
            # https://github.com/mozman/svgwrite/blob/c8cbf6f615910b3818ccf939fce0e407c9c789cb/svgwrite/extensions/inkscape.py#L50
            elements = dwg.validator.elements
            elements['image'].valid_attributes = {'sodipodi:insensitive', } | elements['image'].valid_attributes
            img.attribs['sodipodi:insensitive'] = 'true'

            dwg.save(pretty=True)


cli.add_command(plot)
cli.add_command(digitize)
cli.add_command(cv)
cli.add_command(paginate)


if __name__ == "__main__":
    cli()
