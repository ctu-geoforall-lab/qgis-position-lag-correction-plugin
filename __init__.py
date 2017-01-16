# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PositionCorrection
                                 A QGIS plugin
                             -------------------
        begin                : 2016-02-12
        copyright            : (C) 2016 by Ondřej Pešek
        email                : pesej.ondrek@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load class from file.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .position_correction import PositionCorrection
    return PositionCorrection(iface)
