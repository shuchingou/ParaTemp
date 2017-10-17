#! /usr/bin/env python

########################################################################
#                                                                      #
# This script was written by Thomas Heavey in 2016-17.                 #
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

import glob
import os
import re

import gromacs.formats
import gromacs.tools
import matplotlib.pyplot as plt
import numpy as np
import MDAnalysis

__version__ = '0.0.2'

# todo define a set of run data as a class
# possibly as a class of mdanalysis universes, but not sure how to work with
# replicas vs. walkers there.

# TODO update docstrings to PEP specs
# (one brief description line, blank line, longer description/guidelines)


def find_energies():
    """find_energies() is a function that finds all files in the current
    directory that end in a numeral followed by '.edr'. For each of these
    files, it checks if a file named energy(same number).xvg exists, and if
    not, creates it by calling the GROMACS tool gmx energy where input='13'
    corresponds to the total energy at each time.
    It returns a list of the names of the energy files."""
    energy_files = glob.glob('*[0-9].edr')
    output_files = []
    for file_name in energy_files:
        output_name = ('energy' + re.search('[0-9]*(?=\.edr)',
                                            file_name).group(0) + '.xvg')
        if not os.path.isfile(output_name):
            gromacs.tools.Energy_mpi(f=file_name, o=output_name, input='15')()
        output_files += [output_name]
    output_files.sort()
    output_files.sort(key=len)
    return output_files


def import_energies(output_files, return_lengths=False):
    """import_energies(file_list) takes a list of .xvg files in the current
    directory, imports their second columns (likely a list of energies at
    consecutive time steps), and returns that as a list of arrays."""
    imported_data = []
    lengths = []
    for file_name in output_files:
        xvg_file = gromacs.formats.XVG(filename=file_name)
        imported_data += [xvg_file.array[1]]
        lengths += [len(xvg_file.array[1])]
        # TODO might be faster to find lengths after importing them all
        # call XVG.array may be slow, not really sure
    if return_lengths:
        return imported_data, lengths
    else:
        return imported_data


def make_indices(logfile='npt_PT_out0.log'):
    """make_indices(logfile='npt_PT_out0.log') will check for files named
    'replica_temp.xvg' and 'replica_index.xvg', and if they don't exist will create
    them by calling 'demux.pl [logfile]'.
    It returns nothing."""
    from subprocess import Popen, PIPE
    if not os.path.isfile('replica_temp.xvg'):
        if not os.path.isfile('replica_index.xvg'):
            command_line = ['demux.pl', logfile]
            with open('demux.pl.log', 'w') as log_out_file:
                proc = Popen(command_line, stdout=PIPE, bufsize=1)
                for line in proc.stdout:
                    log_out_file.write(line)


# Run this only if called from the command line
if __name__ == "__main__":
    import argparse
    # todo add argument and code for way to save to a file instead of viewing
    # todo take arguments to change the plotting
    parser = argparse.ArgumentParser(description='A script to plot energy '
                                                 'histograms from a GROMACS '
                                                 'parallel tempering simulation.')
    parser.add_argument('--version', action='version',
                        version='%(prog)s v{}'.format(__version__))
    args = parser.parse_args()

    out_files = find_energies()
    all_data = import_energies(out_files)

    plt.hist(all_data, 50, histtype='stepfilled')

    plt.show()


def combine_energy_files(basename='energy', files=False):
    """combine_energy_files(basename='energy', files=False) is a function that
    combines a set of .xvg files writes a combined .xvg file.
    'basename' is the first part of the name for the xvg files to be combined and
    should differentiate these from any other *.xvg files in the folder.
    Alternatively, the list of files (in the desired order) can be passed in
    with the keyword 'files'.
    Returns None"""
    output_name = basename + '_comb.xvg'
    if os.path.isfile(output_name):
        print('Seems like this has already been run. \n'
              'If you want it run again, change the name or delete '
              'the file named "{}".'.format(output_name))
    else:
        if not files:
            files = glob.glob(basename + '*.xvg')
            files.sort()
            files.sort(key=len)
        imported_data, lengths = import_energies(files, return_lengths=True)
        if all_elements_same(lengths):
            data = [gromacs.formats.XVG(filename=files[0]).array[0]]
            data += imported_data
        else:
            len_shortest = min(lengths)
            data = [gromacs.formats.XVG(filename=files[0]).array[0,
                    :len_shortest]]
            print('Energy lists not all equal lengths. '
                  'Cropping all to the length of the shortest:'
                  ' {}'.format(len_shortest))
            imported_data = [part[:len_shortest] for part in imported_data]
            data += imported_data
        data = np.array(data)
        gromacs.formats.XVG(array=data).write(filename=output_name)
    return None


def all_elements_same(in_list):
    """Check if all list elements the same.

    all_elements_same is a quick function to see if all elements of a list
    are the same. Based on http://stackoverflow.com/a/3844948/3961920
    If they're all the same, returns True, otherwise returns False."""
    return in_list.count(in_list[0]) == len(in_list)


def deconvolve_energies(energyfile='energy_comb.xvg',
                        indexfile='replica_temp.xvg'):
    """deconvolve_energies(energyfile='energy_comb.xvg',
    indexfile='replica_temp.xvg') is a function that takes an xvg file that
    has n columns of energies likely from a replica exchange simulation where each
    replica remains at a constant temperature (as GROMACS does) and using the n
    data columns of an index xvg file returns an array of the energies where each
    row is now from one 'walker' (continuous coordinates taken by sampling various
    temperatures or other replica conditions).
    Each input file is expected to have an index column showing the time step,
    but this index is not included in the output."""
    energies_indexed = gromacs.formats.XVG(filename=energyfile).array
    indices_indexed = gromacs.formats.XVG(filename=indexfile).array.astype(int)
    # todo check for relative start/end points automatically
    length_e = energies_indexed.shape[1]
    length_i = indices_indexed.shape[1]
    ratio = float(length_e) / float(length_i)
    approx_ratio = int(round(ratio))
    if ratio == 1.0:
        deconvolved_energies = energies_indexed[1:][
            indices_indexed[1:],
            np.arange(length_i)]
        e_times = [energies_indexed[0, 0], energies_indexed[0, -1]]
        i_times = [indices_indexed[0, 0], indices_indexed[0, -1]]
    elif ratio > 1:
        if approx_ratio == ratio:
            extra_e = 0
            extra_i = 0
        elif approx_ratio > ratio:
            extra_i = length_i - length_e / approx_ratio
            extra_e = np.mod(length_e, length_i-extra_i)
        elif approx_ratio < ratio:
            extra_e = np.mod(length_e, length_i)
            extra_i = 0
        else:
            raise ImportError('ratio: {}, approx ratio: {}'.format(ratio, approx_ratio))
        # This is dumb! this discards meaningful energies
        # just need to duplicate the index rows for consecutive energy
        # readings between attempted exchanges!
        # todo fix this to not waste energy values
        deconvolved_energies = energies_indexed[1:, :length_e-extra_e:approx_ratio][
            indices_indexed[1:, :length_i-extra_i],
            np.arange((length_i-extra_i))]
        e_times = [energies_indexed[0, :length_e-extra_e:approx_ratio][0],
                   energies_indexed[0, :length_e-extra_e:approx_ratio][-1]]
        i_times = [indices_indexed[0, :length_i-extra_i][0],
                   indices_indexed[0, :length_i-extra_i][-1]]
    elif ratio < 1:
        print('likely undersampling energies because energy / indices ratio is '
              '{}'.format(ratio))
        ratio = 1 / ratio
        approx_ratio = int(round(ratio))
        if approx_ratio == ratio:
            extra_e = 0
            extra_i = 0
        # Not so sure about this...
        elif approx_ratio > ratio:
            extra_e = length_e - length_i / approx_ratio
            extra_i = np.mod(length_i, length_e-extra_e)
        elif approx_ratio < ratio:
            extra_i = np.mod(length_i, length_e)
            extra_e = 0
        else:
            raise ImportError('ratio: {}, approx ratio: {}'.format(ratio, approx_ratio))
        deconvolved_energies = energies_indexed[1:, :length_e-extra_e][
            indices_indexed[1:, :length_i-extra_i:approx_ratio],
            np.arange((length_i-extra_i)/approx_ratio)]
        e_times = [energies_indexed[0, :length_e-extra_e][0],
                   energies_indexed[0, :length_e-extra_e][-1]]
        i_times = [indices_indexed[0, :length_i-extra_i:approx_ratio][0],
                   indices_indexed[0, :length_i-extra_i:approx_ratio][-1]]
    else:
        print('length of energy file is {}'.format(length_e))
        print('length of index file is {}'.format(length_i))
        raise ImportError('Not sure how to handle those values')
    # todo maybe error check is a more pythonic manner with a try/except loop
    # if length_e != length_i:
    #     print("length of energies, {}, != length of indices, "
    #           "{}!".format(length_e, length_i))
    #     raise IndexError('lengths not equals')
    if not (float(e_times[0]) == float(i_times[0]) and
            float(e_times[1]) == float(i_times[1])):
        print('energies start: {}; end: {}'.format(e_times[0], e_times[1]))
        print('indices start: {}; end: {}'.format(i_times[0], i_times[1]))
        print('These values should be about the same if this is working properly')
    return deconvolved_energies


def plot_array(array, index_offset=0, num_replicas=False, n_rows=False, n_cols=False):
    """plot_array(array, index_offset=0, num_replicas=16, n_rows=False, n_cols=False)
    will put each column of array in a different axes of a figure and then return
    the figure."""
    if not num_replicas:
        num_replicas = array.shape[0] - index_offset
    from math import sqrt, ceil
    if n_rows == n_cols == False:
        n_rows = int(ceil(sqrt(float(num_replicas))))
        n_cols = n_rows
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True)
    for i in range(num_replicas):
        ax = axes.flat[i]
        ax.plot(array[i+index_offset])
    return fig


def hist_array(array, index_offset=0, num_replicas=False, n_rows=False, n_cols=False,
               n_bins=10):
    """hist_array(array, index_offset=0, num_replicas=16, n_rows=False, n_cols=False,
    n_bins=10) will put each column of array in a different axes of a figure and
    then return the figure."""
    if not num_replicas:
        num_replicas = array.shape[0] - index_offset
    from math import sqrt, ceil
    if n_rows == n_cols == False:
        n_rows = int(ceil(sqrt(float(num_replicas))))
        n_cols = n_rows
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True)
    for i in range(num_replicas):
        ax = axes.flat[i]
        ax.hist(array[i+index_offset], n_bins)
    return fig


def hist_multi(array, index_offset=1, n_bins=10):
    """hist_multi(array, *kwargs) takes an array and returns a pyplot figure.
    This figure is a histogram of each column of the array in a single pyplot
    axis.
    This is likely most useful for using combined energies from some sort of
    replica exchange method and ensure that the energy histograms have sufficient
    overlap for frequent exchanges"""
    fig, axes = plt.subplots(1, 1)
    axes.hist(array[index_offset:], n_bins, histtype='stepfilled')
    return fig


def solute_trr(trr_base_name='npt_PT_out', tpr_base_name='TOPO/npt',
               output_base_name='solute', index='index.ndx', demux=True,
               group='CHR'):
    """solute_trr takes file base names as input, creates a separate trr file for each
    trajectory that only includes the solutes, and then returns a list of the names of
    the created files.
    If demux=True, it will first use trjcat to deconvolve the walker trajectories (to
    get continuous coordinate files as opposed to continuous temperature).
    This uses gromacswrapper to call trjconv and possibly trjcat."""
    trr_files = glob.glob(trr_base_name + '*.trr')
    trr_files.sort()
    trr_files.sort(key=len)
    tpr_files = glob.glob(tpr_base_name + '*.tpr')
    tpr_files.sort()
    tpr_files.sort(key=len)
    matching_output_name = glob.glob(output_base_name+'*.trr')
    if len(matching_output_name) == len(trr_files):
        print('There are already '
              '{} files matched using "{}".'.format(len(matching_output_name),
                                                    output_base_name) +
              '\nsolute_trr has likely already run.\n'
              'Pick new output name or use current files.')
        matching_output_name.sort()
        matching_output_name.sort(key=len)
        return matching_output_name
    output_files = []
    if demux:
        d_trr_base_name = 'deconv' + trr_base_name
        prev_deconv_files = glob.glob(d_trr_base_name+'*.trr')
        if len(prev_deconv_files) == len(trr_files):
            print('Likely already deconvolved trajectories, skipping that step')
        else:
            gromacs.tools.Trjcat_mpi(f=trr_files, o='demuxed.trr', n='index.ndx',
                                     demux='replica_index.xvg', input=group)()
            trr_files = glob.glob('*demuxed.trr')
            trr_files.sort()
            trr_files.sort(key=len)
            for (i, trr_file) in enumerate(trr_files):
                number = trr_file.split('_')[0]
                new_name = d_trr_base_name + number + '.trr'
                os.rename(trr_file, new_name)
                trr_files[i] = new_name
        trr_base_name = d_trr_base_name
    if len(trr_files) != len(tpr_files):
        raise IndexError('Number of trr and tpr files not equal: '
                         '{} and {}'.format(len(trr_files), len(tpr_files)))
    for (i, trr_name) in enumerate(trr_files):
        number_match = re.search('(?:'+trr_base_name+')(\d+)(?:\.trr)', trr_name)
        number = number_match.group(1)
        out_file = output_base_name + number + '.trr'
        output_files.append(out_file)
        gromacs.tools.Trjconv_mpi(s=tpr_files[i], pbc='mol', f=trr_name, o=out_file,
                                  n=index, center=True, input=(group, group))()
    return output_files


def radii_of_gyration(basename='solute', atom_selection=False, resname='TAD',
                      gro_file='geom-solutes.gro'):
    """A function to find the radius of gyration for all timesteps for a set of
    REMD trajectories.
    The basename is the name before the numbers for the trajectory files.
    resname is the name of the desired residue to be selected.
    A more general atom_selection can be given, in which case resname will
    be ignored.
    Assumes all trajectories are the same length.
    Returns the values as a numpy array."""
    u_solutes = []
    files = glob.glob(basename+'*.trr')
    num_files = len(files)
    for file_name in files:
        u_solutes.append(MDAnalysis.Universe(gro_file, file_name))
    rgs = np.zeros((num_files, len(u_solutes[0].trajectory)))
    if not atom_selection:
        selection = 'resname ' + resname
    else:
        selection = atom_selection
    for (i, u) in enumerate(u_solutes):
        tad = u.select_atoms(selection)
        for fr in u.trajectory:
            rgs[i, fr.frame] = tad.radius_of_gyration()
    return rgs

# TODO write function to estimate tunneling times
# TODO write function to find average exchange time/prob?


def make_basic_plots(save_base_name='pt', save=True, save_format='.pdf',
                     display=True, logfile='npt_PT_out0.log'):
    """make_basic_plots takes keyword arguments to find the energies for replica
    exchange simulations in order to make basic plots of the energies.
    The three plots made are a combined histogram of the replica energies,
    separate histograms of the walker energies, and separate plots of the
    replica energies as a function of time.
    If save=True, the plots will be written to disk.
    If display=True, the figures will be returned as a list so they can be
    displayed or edited. Returned in the order walker plots, walker histograms,
    replica histogram. If display=False, returns None.
    Uses the functions in this package find_energies, combine_energy_files,
    make_indices, deconvolve_energies, plot_array, hist_array, hist_multi."""
    # TODO find some way to take arguments for the plotting functions
    # would need to do the same in the plotting functions this calls
    # **keywords should work
    find_energies()
    combine_energy_files()
    make_indices(logfile=logfile)
    deconvolved_energies = deconvolve_energies()
    deconvolved_energies_of_time_fig = plot_array(deconvolved_energies)
    deconvolved_energies_of_time_fig.text(0.1, 0.55, 'energy', ha='center',
                                          rotation='vertical')
    deconvolved_energies_of_time_fig.text(0.515, 0.08, 'time', ha='center')
    for ax in deconvolved_energies_of_time_fig.axes:
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
    deconvolved_energies_hist_fig = hist_array(deconvolved_energies)
    deconvolved_energies_hist_fig.text(0.1, 0.53, 'count', ha='center',
                                       rotation='vertical')
    deconvolved_energies_hist_fig.text(0.51, 0.08, 'energy', ha='center')
    for ax in deconvolved_energies_hist_fig.axes:
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
    combined_energies = gromacs.formats.XVG(filename='energy_comb.xvg').array
    repl_ener_hist = hist_multi(combined_energies[1:].transpose(),
                                index_offset=0, n_bins=100)
    ax = repl_ener_hist.gca()
    ax.set_ylabel('count')
    ax.set_xlabel('energy')
    if save:
        deconvolved_energies_of_time_fig.savefig(save_base_name+'_e_of_t'+save_format)
        deconvolved_energies_hist_fig.savefig(save_base_name+'_e_hists'+save_format)
        repl_ener_hist.savefig(save_base_name+'_repl_e_hists'+save_format)
    if display:
        return [deconvolved_energies_of_time_fig, deconvolved_energies_hist_fig,
                repl_ener_hist]
    else:
        return None


def make_rg_figures(save_base_name='pt', save=True, save_format='.pdf',
                    display=True, group='TAD', gro_file='npt_PT_out0.gro'):
    """make_rg_figures will take a set of trajectories, run solute_trr on them
    (to separate out the solutes and remove excess motion) then make a plot of
    the radius of gyration for each walker as a function of time and histograms
    of those as well.
    If display=True, a list of the two figures will be returned; if
    display=False, None will be returned.
    If save=True, the figures will also be saved to the cwd."""
    # create get solute only trajectories
    # trr_names = solute_trr(group=group)
    solute_trr(group=group)
    rgs = radii_of_gyration(gro_file=gro_file)
    rgs_t_plots = plot_array(rgs)
    rgs_t_plots.text(0.1, 0.51, '$R_G$', usetex=True, ha='center', rotation='vertical')
    rgs_t_plots.text(0.515, 0.07, 'time', ha='center')
    for ax in rgs_t_plots.axes:
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
    rgs_hists = hist_array(rgs)
    rgs_hists.text(0.1, 0.53, 'count', ha='center', rotation='vertical')
    rgs_hists.text(0.5, 0.1, '$R_G$', usetex=True)
    for ax in rgs_hists.axes:
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
    if save:
        rgs_t_plots.savefig(save_base_name+'rgs_of_t'+save_format)
        rgs_hists.savefig(save_base_name+'rgs_hists'+save_format)
    if display:
        return [rgs_t_plots, rgs_hists]
    else:
        return None