"""This contains a set of tests for paratemp.sim_setup.Simulation"""

########################################################################
#                                                                      #
# This script was written by Thomas Heavey in 2018.                    #
#        theavey@bu.edu     thomasjheavey@gmail.com                    #
#                                                                      #
# Copyright 2017-18 Thomas J. Heavey IV                                #
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

import os
import pathlib
import pytest
import re

from paratemp.tools import cd


@pytest.mark.xfail
class TestSimulation(object):

    def test_runs(self, pt_blank_dir):
        from paratemp.sim_setup import Simulation
        gro = pt_blank_dir / 'PT-out0.gro'
        top = pt_blank_dir / 'spc-and-methanol.top'
        sim = Simulation(name='test_sim',
                         gro=gro, top=top, base_folder=pt_blank_dir)
        assert isinstance(sim, Simulation)

    @pytest.fixture
    def mdps(self):
        min_mdp = 'examples/sample-mdps/minim.mdp'
        equil_mdp = 'examples/sample-mdps/equil.mdp'
        prod_mdp = 'examples/sample-mdps/prod.mdp'
        mdps = dict(minimize=min_mdp, equilibrate=equil_mdp,
                    production=prod_mdp)
        return mdps

    @pytest.fixture
    def sim(self, pt_blank_dir, mdps):
        from paratemp.sim_setup import Simulation
        gro = pt_blank_dir / 'PT-out0.gro'
        top = pt_blank_dir / 'spc-and-methanol.top'
        sim = Simulation(name='sim_fixture',
                         gro=gro, top=top, base_folder=pt_blank_dir,
                         mdps=mdps)
        return sim

    attrs = {'name': str,
             'top': pathlib.Path,
             'base_folder': pathlib.Path,
             'mdps': dict,
             'tprs': dict,
             'deffnms': dict,
             'outputs': dict,
             }

    def test_attrs_exist(self, sim):
        for attr in self.attrs:
            assert hasattr(sim, attr)
            dtype = self.attrs[attr]
            assert isinstance(getattr(sim, attr), dtype)

    def test_methods_exist(self, sim, mdps):
        for step in mdps:
            assert hasattr(sim, step)
            assert callable(getattr(sim, step))
