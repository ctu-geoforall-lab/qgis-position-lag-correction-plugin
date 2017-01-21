.. SuroLeveling documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

QGIS Plugin GPS Position Lag Correction Documentation
=====================================================

Description
***********

The plugin allows user to correct a record delay of points in QGIS. User is
allowed to shift points by values, by constant distance or by constant time
(variable distance considering current velocity). Ellipsoid WGS84 (EPSG:4326)
is used as a reference ellipsoid.

Loading of plugin
*****************
There are many ways to install the plugin. The easiest method is to install
it from the QGIS Plugin repository.

Firstly, you have to open the plugins dialog – select
``Manage and install plugins`` from
``Plugins`` tab.

Search for ``GPS Position Lag Correction`` plugin in
the list on the ``All`` or ``Not installed`` tab.
Select it and press the ``Install`` button.

Work with plugin
****************

.. figure:: screenshot-gui.png

   *Fig 1: GUI*

Input and output
----------------
As input, you have to define the file you want to work
with. You can write the path to this file manually or
use the button with ``...``. By clicking
on this button, you will get the dialog intended to
choose your file. Click on OK will insert this path
to the basic interface. Click
on Cancel will interrupt the choosing dialog,
and the input path will not be changed.

The same procedure is with output, but there you define
the path where the new file will be created.
The choosing dialog for output is intended to
choose folder, not file.

::

   Input CSV contents
   lat_deg:    Latitude of point (EPSG:4326)
   lon_deg:    Longitude of point (EPS:4326)
   Gtm_sec:    Time stamp of measuring in seconds

There is also an optional possibility of styling your points
for better visualisation.

By default, you have not defined any style
and points will be created in the default QGIS style
(on Style button is written ``No style``)
If you want your own style, you have to click on
this button. You will get the browsing dialog.
You are automatically directed to folder
``styles`` in the plugin folder; here you can
choose qml file and click OK. Click on Cancel
interrupts the dialog and sets again ``No style``.
If you choose your own style, you will see its name on the style button.

In the default plugin version there are two presetted styles.
User is allowed to import his own styles. Styling is based on the value in
column ``mereni``.

If user prefers to visualise both the input and the output from one dialog,
it is allowed by the ``Show`` button. Input layer is also styled and it gives
user the opportunity to compary the shifted values with the original ones.

.. figure:: screenshot-styled.png

   *Fig 2: Styled input*

Shift
-----
Shift is done by clicking on the button ``Solve``. User should define value of
shif and can choose units - values, meters (distance) or seconds (variable
distance considering current velocity). Points are shifted on a trajectory.

.. figure:: screenshot-shifted.png

   *Fig 3: Red ones shifted by 1.14 seconds*


Authors
*******

* Ondrej Pesek

`GeoForAll Laboratory <http://geomatics.fsv.cvut.cz/research/osgeorel/>`__ at
Czech Technical University in Prague, Czech Republic

In collaboration with `SURO <http://www.suro.cz>`__

Under supervison of Martin Landa

Licence
^^^^^^^

Source code (https://github.com/ctu-geoforall-lab/qgis-position-lag-correction-plugin) licenced under GNU GPL 3.

Report bugs
^^^^^^^^^^^

Please report bugs at https://github.com/ctu-geoforall-lab/qgis-position-lag-correction-plugin/issues
