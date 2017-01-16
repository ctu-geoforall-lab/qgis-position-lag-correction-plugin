# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Move (the main file)
                                 A QGIS plugin
 This script contains all three types of shifts: By points, meters or seconds
        everything made on ellipsoid WGS-84
                             -------------------
        begin                : 2016-02-12
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Ondřej Pešek
        email                : pesej.ondrek@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import QgsDistanceArea, QgsPoint
from math import sqrt, pi, pow, fabs, sin, cos, tan, ceil

import time


class MoveError(StandardError):
    pass


class Move:
    def __init__(self, inputfile, outputfile):
        self.inputfile = open(inputfile, 'rb')
        self.outputfile = open(outputfile, 'wb')

    def _close(self):
        for f in (self.inputfile, self.outputfile):
            if not f.closed:
                f.close()

    def _check(self):
        if not self.inputfile or self.inputfile.closed:
            raise MoveError("Input file is not open")

        if not self.outputfile or self.outputfile.closed:
            raise MoveError("Output file is not open")

    def iterations(self, distance, a, e2, h, azi, fi, lam):
        """
        iterations needed to solve the first geodetic problem
        :param distance: distance used to shift point by
        :param a: main axis of ellipsoid
        :param e2: excentricity of ellipsoid
        :param h: step to approximate the curve
        :param azi: original azimuth in the point assigned to shift
        :param fi: original latitude of the point assigned to shift
        :param lam: original longitude of the point assigned to shift
        :return FIe1: new latitude of point
        :return LAMe1: new longitude of point
        """

        FIe1 = 0
        LAMe1 = 0
        FI = 100
        LAM = 100

        # iterations
        while fabs(FI-FIe1) > 0.0000000001 and fabs(LAM-LAMe1) > 0.0000000001:
            FI = FIe1
            LAM = LAMe1
            for i in range(0, int(ceil(distance/h))):
                kfi = []
                klam = []
                kazi = []
                kfi.append(cos(azi[i])/(a*(1-(e2))/(pow((sqrt(1-(e2)*pow(sin(fi[i]), 2))), 3))))
                klam.append(sin(azi[i])/((a/(sqrt(1-(e2)*pow(sin(fi[i]), 2))))*cos(fi[i])))
                kazi.append(sin(azi[i])*tan(fi[i])/(a/(sqrt(1-(e2)*pow(sin(fi[i]), 2)))))
                for j in range(1, 3):
                    kfi.append(cos(azi[i]+kazi[j-1]*h/2)/(a*(1-(e2))/(pow(sqrt(1-(e2)*pow(sin(fi[i]+kfi[j-1]*h/2), 2)), 3))))
                    klam.append(sin(azi[i]+kazi[j-1]*h/2)/((a/(sqrt(1-(e2)*pow(sin(fi[i]+kfi[j-1]*h/2), 2))))*cos(fi[i]+kfi[j-1]*h/2)))
                    kazi.append(sin(azi[i]+kazi[j-1]*h/2)*tan(fi[i]+kfi[j-1]*h/2)/(a/(sqrt(1-(e2)*pow(sin(fi[i]+kfi[j-1]*h/2), 2)))))

                kfi.append(cos(azi[i]+kazi[2]*h)/(a*(1-(e2))/(pow(sqrt(1-(e2)*pow(sin(fi[i]+kfi[2]*h), 2)), 3))))
                klam.append(sin(azi[i]+kazi[2]*h)/((a/(sqrt(1-(e2)*pow(sin(fi[i]+kfi[2]*h), 2))))*cos(fi[i]+kfi[2]*h)))
                kazi.append(sin(azi[i]+kazi[2]*h)*tan(fi[i]+kfi[2]*h)/(a/(sqrt(1-(e2)*pow(sin(fi[i]+kfi[2]*h), 2)))))

                fi.append(fi[i]+(h/6.0)*(kfi[0]+2*kfi[1]+2*kfi[2]+kfi[3]))
                lam.append(lam[i]+(h/6.0)*(klam[0]+2*klam[1]+2*klam[2]+klam[3]))
                azi.append(azi[i]+(h/6.0)*(kazi[0]+2*kazi[1]+2*kazi[2]+kazi[3]))

            FIe1 = fi[i+1]
            LAMe1 = lam[i+1]
            h = h/2
            fi[1:] = []
            lam[1:] = []
            azi[1:] = []

        return FIe1, LAMe1

    def by_points(self, value):
        """
        shift by number of points
        :param value: number of points used to shift (int)
        """

        self._check()

        header = self.inputfile.readline()
        self.outputfile.write(header)
        beforeLat_deg = header.split('Lat_deg')
        beforeLon_deg = header.split('Lon_deg')
        numberOfLat_degColumn = beforeLat_deg[0].split(',')
        numberOfLon_degColumn = beforeLon_deg[0].split(',')

        if value > 0:
            outline = self.inputfile.readline()

            while outline:
                linePos = self.inputfile.tell()
                for i in range(value):
                    line = self.inputfile.readline()

                outline = outline.split(',')
                line = line.split(',')
                try:
                    outline[len(numberOfLat_degColumn)-1] = line[
                        len(numberOfLat_degColumn)-1]
                    outline[len(numberOfLon_degColumn)-1] = line[
                        len(numberOfLon_degColumn)-1]
                except:
                    break
                outline = ','.join(outline)
                self.outputfile.write(outline)
                self.inputfile.seek(linePos)
                outline = self.inputfile.readline()

        elif value < 0:
            line = []
            for i in range(abs(value)+1):
                line.append(self.inputfile.readline())
                line[i] = line[i].split(',')

            while line[i] != ['']:
                outline = 1*line[i]
                outline[len(numberOfLat_degColumn)-1] = line[0][
                    len(numberOfLat_degColumn)-1]
                outline[len(numberOfLon_degColumn)-1] = line[0][
                    len(numberOfLon_degColumn)-1]

                outline = ','.join(outline)
                self.outputfile.write(outline)
                del line[0]
                line.append(self.inputfile.readline())
                line[i] = line[i].split(',')

        else:
            a = self.inputfile.readline()
            while a:
                self.outputfile.write(a)
                a = self.inputfile.readline()

        self._close()

    def by_distance(self, distance):
        """
        shift by constant distance
        :param distance: distance used to shift in meters
        """

        self._check()
        header = self.inputfile.readline()
        beforeLat = header.split('Lat_deg')
        numberOfLatColumn = beforeLat[0].split(',')
        beforeLong = header.split('Lon_deg')
        numberOfLonColumn = beforeLong[0].split(',')
        self.outputfile.write(header)

        d = QgsDistanceArea()
        d.setEllipsoid('WGS84')
        d.setEllipsoidalMode(True)
        d.ellipsoid()
        a = 6378137.0  # WGS84 ellipsoid parametres
        e2 = 0.081819190842622
        line1 = self.inputfile.readline()

        if distance > 0:
            linePos = self.inputfile.tell()
            line1 = line1.split(',')
            while line1:
                self.inputfile.seek(linePos)
                line2 = self.inputfile.readline()
                linePos = self.inputfile.tell()
                moveDistance = 1*distance
                outline = 1*line1
                inline = line2.split(',')

                if line2:
                    line2 = line2.split(',')
                    p1 = QgsPoint(float(line1[len(numberOfLonColumn)-1]),
                                  float(line1[len(numberOfLatColumn)-1]))
                    p2 = QgsPoint(float(line2[len(numberOfLonColumn)-1]),
                                  float(line2[len(numberOfLatColumn)-1]))
                    l = d.computeDistanceBearing(p1, p2)[0]

                    while moveDistance > l:
                        if line2:
                            moveDistance = moveDistance-l
                            line1 = 1*line2
                            line2 = self.inputfile.readline()
                            if line2:
                                line2 = line2.split(',')
                                p1 = QgsPoint(
                                    float(line1[len(numberOfLonColumn)-1]),
                                    float(line1[len(numberOfLatColumn)-1]))
                                p2 = QgsPoint(
                                    float(line2[len(numberOfLonColumn)-1]),
                                    float(line2[len(numberOfLatColumn)-1]))
                                l = d.computeDistanceBearing(p1, p2)[0]
                        else:
                            break

                    if line2:
                        if moveDistance != l:
                            if p1 != p2:
                                aziA = d.bearing(p1, p2)

                                h = moveDistance/2.0
                                fi = [float(
                                    line1[len(numberOfLatColumn)-1])*pi/180]
                                lam = [float(
                                    line1[len(numberOfLonColumn)-1])*pi/180]
                                azi = [aziA]

                                FIe1, LAMe1 = self.iterations(
                                    moveDistance, a, e2, h, azi, fi, lam)
                            else:
                                FIe1 = float(
                                    line2[len(numberOfLatColumn)-1])*pi/180
                                LAMe1 = float(
                                    line2[len(numberOfLonColumn)-1])*pi/180

                        else:
                            FIe1 = float(
                                line2[len(numberOfLatColumn)-1])*pi/180
                            LAMe1 = float(
                                line2[len(numberOfLonColumn)-1])*pi/180

                        # changing latitude and longitude of new point
                        outline[len(numberOfLatColumn)-1] = str(FIe1*180/pi)
                        outline[len(numberOfLonColumn)-1] = str(LAMe1*180/pi)
                        outline = ','.join(outline)
                        self.outputfile.write(outline)
                        line1 = inline
                    else:
                        break

                else:
                    break

        elif distance < 0:
            line = []
            line.append(line1)
            line[0] = line[0].split(',')
            line.append(self.inputfile.readline())
            line[1] = line[1].split(',')
            i = 1
            distance = fabs(distance)
            moveDistance = fabs(distance)
            p1 = QgsPoint(float(line[0][len(numberOfLonColumn)-1]),
                          float(line[0][len(numberOfLatColumn)-1]))
            p2 = QgsPoint(float(line[1][len(numberOfLonColumn)-1]),
                          float(line[1][len(numberOfLatColumn)-1]))
            allDist = d.computeDistanceBearing(p1, p2)[0]
            while moveDistance > allDist:
                line.append(self.inputfile.readline().split(','))
                i = i+1
                if line[len(line)-1] == ['']:
                    break
                p1 = QgsPoint(float(line[i-1][len(numberOfLonColumn)-1]),
                              float(line[i-1][len(numberOfLatColumn)-1]))
                p2 = QgsPoint(float(line[i][len(numberOfLonColumn)-1]),
                              float(line[i][len(numberOfLatColumn)-1]))
                allDist = allDist+d.computeDistanceBearing(p1, p2)[0]

            while line[len(line)-1] != ['']:
                allDist = 0
                for i in reversed(range(1, len(line))):
                    p1 = QgsPoint(float(line[i-1][len(numberOfLonColumn)-1]),
                                  float(line[i-1][len(numberOfLatColumn)-1]))
                    p2 = QgsPoint(float(line[i][len(numberOfLonColumn)-1]),
                                  float(line[i][len(numberOfLatColumn)-1]))
                    allDist = allDist+d.computeDistanceBearing(p1, p2)[0]
                    if fabs(moveDistance) <= allDist:
                        for x in range(i-1):
                            del line[0]
                        break

                for i in reversed(range(len(line))):
                    p1 = QgsPoint(float(line[i-1][len(numberOfLonColumn)-1]),
                                  float(line[i-1][len(numberOfLatColumn)-1]))
                    p2 = QgsPoint(float(line[i][len(numberOfLonColumn)-1]),
                                  float(line[i][len(numberOfLatColumn)-1]))

                    if p1 != p2:
                        aziA = d.bearing(p2, p1)
                        l = d.computeDistanceBearing(p1, p2)[0]

                        if moveDistance > l:
                            moveDistance = moveDistance-l
                        elif moveDistance != 0 and moveDistance != l:
                            # first geodetic problem
                            h = moveDistance/2.0
                            fi = [float(
                                line[i][len(numberOfLatColumn)-1])*pi/180]
                            lam = [float(
                                line[i][len(numberOfLonColumn)-1])*pi/180]
                            azi = [aziA]

                            FIe1, LAMe1 = self.iterations(
                                moveDistance, a, e2, h, azi, fi, lam)
                            break

                        else:
                            FIe1 = float(
                                line[i-1][len(numberOfLatColumn)-1])*pi/180
                            LAMe1 = float(
                                line[i-1][len(numberOfLonColumn)-1])*pi/180
                            break
                    else:
                        if moveDistance > l:
                            moveDistance = moveDistance-l
                        else:
                            FIe1 = float(
                                line[i-1][len(numberOfLatColumn)-1])*pi/180
                            LAMe1 = float(
                                line[i-1][len(numberOfLonColumn)-1])*pi/180
                            break

                outline = 1*line[len(line)-1]
                # changing latitude and longitude of new point
                outline[len(numberOfLatColumn)-1] = str(FIe1*180/pi)
                outline[len(numberOfLonColumn)-1] = str(LAMe1*180/pi)
                outline = ','.join(outline)
                self.outputfile.write(outline)

                line.append(self.inputfile.readline())
                line[len(line)-1] = line[len(line)-1].split(',')
                moveDistance = fabs(distance)
        else:
            while line1:
                self.outputfile.write(line1)
                line1 = self.inputfile.readline()

        self._close()

    def by_seconds(self, seconds):
        """
        shift by variable distance
        :param seconds: number of seconds used to calculate velocity
        """

        self._check()
        header = self.inputfile.readline()
        beforeLat = header.split('Lat_deg')
        numberOfLatColumn = beforeLat[0].split(',')
        beforeLong = header.split('Lon_deg')
        numberOfLonColumn = beforeLong[0].split(',')
        beforeSec = header.split('Gtm_sec')
        numberOfSecColumn = beforeSec[0].split(',')
        self.outputfile.write(header)

        d = QgsDistanceArea()
        d.setEllipsoid('WGS84')
        d.setEllipsoidalMode(True)
        d.ellipsoid()
        a = 6378137.0  # WGS84 ellipsoid parametres
        e2 = 0.081819190842622
        line1 = self.inputfile.readline()

        if seconds > 0:
            linePos = self.inputfile.tell()
            line1 = line1.split(',')
            while line1:
                self.inputfile.seek(linePos)
                line2 = self.inputfile.readline()
                linePos = self.inputfile.tell()
                moveTime = 1*seconds
                outline = 1*line1
                inline = line2.split(',')

                while moveTime > 0:  # for case of more than 1 second
                    if line2:
                        line2 = line2.split(',')
                        p1 = QgsPoint(float(line1[len(numberOfLonColumn)-1]),
                                      float(line1[len(numberOfLatColumn)-1]))
                        p2 = QgsPoint(float(line2[len(numberOfLonColumn)-1]),
                                      float(line2[len(numberOfLatColumn)-1]))

                        if p1 != p2:
                            aziA = d.bearing(p1, p2)
                            l = d.computeDistanceBearing(p1, p2)[0]

                            if moveTime > (float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1])):
                                moveTime = moveTime-(float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1]))
                            elif moveTime != 0 and moveTime != (float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1])):
                                # first geodetic problem
                                distance = l/(float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1]))*moveTime
                                h = distance/2.0
                                fi = [float(
                                    line1[len(numberOfLatColumn)-1])*pi/180]
                                lam = [float(
                                    line1[len(numberOfLonColumn)-1])*pi/180]
                                azi = [aziA]

                                FIe1, LAMe1 = self.iterations(
                                    distance, a, e2, h, azi, fi, lam)
                                moveTime = 0

                            else:
                                FIe1 = float(
                                    line2[len(numberOfLatColumn)-1])*pi/180
                                LAMe1 = float(
                                    line2[len(numberOfLonColumn)-1])*pi/180
                                moveTime = 0
                                break
                        else:
                            if moveTime > (float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1])):
                                moveTime = moveTime-(float(line2[len(numberOfSecColumn)-1])-float(line1[len(numberOfSecColumn)-1]))
                            else:
                                FIe1 = float(
                                    line2[len(numberOfLatColumn)-1])*pi/180
                                LAMe1 = float(
                                    line2[len(numberOfLonColumn)-1])*pi/180
                                moveTime = 0
                                break

                    else:
                        break
                    line1 = 1*line2
                    line2 = self.inputfile.readline()

                line1 = 1*inline
                if moveTime == 0:
                    # changing latitude and longitude of new point
                    outline[len(numberOfLatColumn)-1] = str(FIe1*180/pi)
                    outline[len(numberOfLonColumn)-1] = str(LAMe1*180/pi)
                    outline = ','.join(outline)
                    self.outputfile.write(outline)
                else:
                    break

        elif seconds < 0:
            line = []
            line.append(line1)
            line[0] = line[0].split(',')
            line.append(self.inputfile.readline())
            line[1] = line[1].split(',')
            allSecs = (float(line[1][len(numberOfSecColumn)-1])-float(line[0][len(numberOfSecColumn)-1]))
            i = 1
            moveTime = 1*seconds
            while fabs(moveTime) > allSecs:
                line.append(self.inputfile.readline().split(','))
                i = i+1
                if line[len(line)-1] == ['']:
                    break
                allSecs = allSecs+(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1]))

            while line[len(line)-1] != ['']:
                allSecs = 0
                for i in reversed(range(1, len(line))):
                    allSecs = allSecs+(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1]))
                    if fabs(moveTime) <= allSecs:
                        for x in range(i-1):
                            del line[0]
                        break

                for i in reversed(range(len(line))):
                    p1 = QgsPoint(float(line[i-1][len(numberOfLonColumn)-1]),
                                  float(line[i-1][len(numberOfLatColumn)-1]))
                    p2 = QgsPoint(float(line[i][len(numberOfLonColumn)-1]),
                                  float(line[i][len(numberOfLatColumn)-1]))

                    if p1 != p2:
                        aziA = d.bearing(p2, p1)
                        l = d.computeDistanceBearing(p1, p2)[0]

                        if moveTime < -(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1])):
                            moveTime = moveTime+(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1]))
                        elif moveTime != 0 and moveTime != -(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1])):
                            # first geodetic problem
                            distance = l/(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1]))*fabs(moveTime)
                            h = distance/2.0
                            fi = [float(
                                line[i][len(numberOfLatColumn)-1])*pi/180]
                            lam = [float(
                                line[i][len(numberOfLonColumn)-1])*pi/180]
                            azi = [aziA]

                            FIe1, LAMe1 = self.iterations(
                                distance, a, e2, h, azi, fi, lam)
                            break

                        else:
                            FIe1 = float(
                                line[i-1][len(numberOfLatColumn)-1])*pi/180
                            LAMe1 = float(
                                line[i-1][len(numberOfLonColumn)-1])*pi/180
                            break
                    else:
                        if moveTime < -(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1])):
                            moveTime = moveTime+(float(line[i][len(numberOfSecColumn)-1])-float(line[i-1][len(numberOfSecColumn)-1]))
                        else:
                            FIe1 = float(
                                line[i-1][len(numberOfLatColumn)-1])*pi/180
                            LAMe1 = float(
                                line[i-1][len(numberOfLonColumn)-1])*pi/180
                            break

                outline = 1*line[len(line)-1]
                # changing latitude and longitude of new point
                outline[len(numberOfLatColumn)-1] = str(FIe1*180/pi)
                outline[len(numberOfLonColumn)-1] = str(LAMe1*180/pi)
                outline = ','.join(outline)
                self.outputfile.write(outline)

                line.append(self.inputfile.readline())
                line[len(line)-1] = line[len(line)-1].split(',')
                moveTime = 1*seconds

        else:
            while line1:
                self.outputfile.write(line1)
                line1 = self.inputfile.readline()

        self._close()
