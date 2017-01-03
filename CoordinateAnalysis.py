#! /usr/bin/env python

########################################################################
#                                                                      #
# This script was written by Thomas Heavey in 2017.                    #
#        theavey@bu.edu     thomasjheavey@gmail.com                    #
#                                                                      #
# Copyright 2017 Thomas J. Heavey IV                                   #
#                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");      #
# you may not use this file except in compliance with the License.     #
# You may obtain a copy of the License at                              #
#                                                                      #
#    http://www.apache.org/licenses/LICENSE-2.0                        #
#                                                                      #
# Unless required by applicable law or agreed to in writing, software  #
# distributed under the License is distributed on an "AS IS" BASIS,    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or      #
# implied.                                                             #
# See the License for the specific language governing permissions and  #
# limitations under the License.                                       #
#                                                                      #
########################################################################

from __future__ import absolute_import
from .exceptions import InputError


def get_taddol_selections(universe, univ_in_dict=True):
    """Returns a dict of AtomSelections from the given universe"""
    d_out = dict()
    if univ_in_dict:
        d_out['universe'] = universe
    d_out["phenrtt"] = universe.select_atoms('bynum 92 94')
    d_out["phenrtb"] = universe.select_atoms('bynum 82 87')
    d_out["phenrbt"] = universe.select_atoms('bynum 69 71')
    d_out["phenrbb"] = universe.select_atoms('bynum 59 64')
    d_out["phenltt"] = universe.select_atoms('bynum 115 117')
    d_out["phenltb"] = universe.select_atoms('bynum 105 110')
    d_out["phenlbt"] = universe.select_atoms('bynum 36 41')
    d_out["phenlbb"] = universe.select_atoms('bynum 46 48')
    d_out["quatl"] = universe.select_atoms('bynum 6')
    d_out["quatr"] = universe.select_atoms('bynum 1')
    d_out["chirl"] = universe.select_atoms('bynum 4')
    d_out["chirr"] = universe.select_atoms('bynum 2')
    d_out["cyclon"] = universe.select_atoms('bynum 13')
    d_out["cyclof"] = universe.select_atoms('bynum 22')
    d_out["aoxl"] = universe.select_atoms('bynum 9')
    d_out["aoxr"] = universe.select_atoms('bynum 7')
    return d_out


def get_dist(a, b):
    """Calculate the distance between AtomGroups a and b"""
    from numpy.linalg import norm
    return norm(a.centroid() - b.centroid())


def get_dist_dict(dictionary, a, b):
    """Calculate distance using dict of AtomSelections"""
    return get_dist(dictionary[a], dictionary[b])


def get_angle(a, b, c, units='rad'):
    """Calculate the angle between ba and bc for AtomGroups a, b, c"""
    from numpy import arccos, rad2deg, dot
    from numpy.linalg import norm
    b_center = b.centroid()
    ba = a.centroid() - b_center
    bc = c.centroid() - b_center
    angle = arccos(dot(ba, bc)/(norm(ba)*norm(bc)))
    if units == 'rad':
        return angle
    elif units == 'deg':
        return rad2deg(angle)
    else:
        raise InputError(units,
                         'Unrecognized units: '
                         'the two recognized units are rad and deg.')


def get_angle_dict(dictionary, a, b, c, units='rad'):
    """Calculate angle using dict of AtomSelections"""
    return get_angle(dictionary[a], dictionary[b], dictionary[c],
                     units=units)


def get_dihedral(a, b, c, d, units='rad'):
    """Calculate the angle between abc and bcd for AtomGroups a,b,c,d

    Based on formula given in
    https://en.wikipedia.org/wiki/Dihedral_angle"""
    from numpy import cross, arctan2, dot, rad2deg
    from numpy.linalg import norm
    ba = a.centroid() - b.centroid()
    bc = b.centroid() - c.centroid()
    dc = d.centroid() - c.centroid()
    angle = arctan2(dot(cross(cross(ba, bc), cross(bc, dc)), bc) /
                    norm(bc), dot(cross(ba, bc), cross(bc, dc)))
    if units == 'rad':
        return angle
    elif units == 'deg':
        return rad2deg(angle)
    else:
        raise InputError(units,
                         'Unrecognized units: '
                         'the two recognized units are rad and deg.')


def get_dihedral_dict(dictionary, a, b, c, d, units='rad'):
    """Calculate dihedral using dict of AtomSelections"""
    return get_dihedral(dictionary[a], dictionary[b],
                        dictionary[c], dictionary[d],
                        units=units)


def get_taddol_ox_dists(universe, sel_dict=False):
    """Get array of oxygen distances in TADDOL trajectory"""
    from numpy import array
    if not sel_dict:
        sel_dict = get_taddol_selections(universe)
    output = []
    for frame in universe.trajectory:
        output.append((universe.trajectory.time,
                       get_dist_dict(sel_dict, 'aoxl', 'aoxr'),
                       get_dist_dict(sel_dict, 'aoxl', 'cyclon'),
                       get_dist_dict(sel_dict, 'aoxr', 'cyclon')))
    return array(output)


def make_plot_taddol_ox_dists(data, save=False, save_format='pdf',
                              save_base_name='ox_dists',
                              display=True):
    """"""
    from matplotlib.pyplot import subplots
    fig, axes = subplots()
    axes.plot(data[:, 0], data[:, 1], label='O-O')
    axes.plot(data[:, 0], data[:, 2], label='O(l)-Cy')
    axes.plot(data[:, 0], data[:, 3], label='O(r)-Cy')
    axes.legend()
    axes.set_xlabel('time / ps')
    axes.set_ylabel('distance / $\mathrm{\AA}$')
    if save:
        fig.savefig(save_base_name+save_format)
    if display:
        return fig
    else:
        return None
