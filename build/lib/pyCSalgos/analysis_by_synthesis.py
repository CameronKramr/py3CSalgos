"""
analysis_by_synthesis.py

Perform analysis-based recovery based on synthesis recovery
"""

import numpy as np

from .base import AnalysisSparseSolver, SparseSolver


class AnalysisBySynthesis(AnalysisSparseSolver):

    # All parameters related to the algorithm itself are given here.
    # The data and dictionary are given to the solve() method
    def __init__(self, synthesis_solver, nullspace_multiplier=1, nullspace_multiplier_type='normalized_row'):

        assert isinstance(synthesis_solver, SparseSolver)
        self.synthsolver = synthesis_solver
        self.nullspace_multiplier = nullspace_multiplier
        self.nullspace_multiplier_type = nullspace_multiplier_type

    def __str__(self):
        return "AbS (" + str(self.synthsolver) + ", " + str(self.nullspace_multiplier) + ")"

    def solve(self, measurements, acqumatrix, operator, realdict):

        # Ensure measurements 2D
        if len(measurements.shape) == 1:
            data = np.atleast_2d(measurements)
            if measurements.shape[0] < measurements.shape[1]:
                measurements = np.transpose(measurements)

        operatorsize, signalsize = operator.shape
        # Find nullspace
        dictionary = np.linalg.pinv(operator)
        U,S,Vt = np.linalg.svd(dictionary)
        nullspace = Vt[-(operatorsize-signalsize):, :]
        # Create aggregate dictionary
        mul = self.compute_multiplier(measurements, acqumatrix, operator)
        Atilde = np.vstack((np.dot(acqumatrix, dictionary), mul * nullspace))
        ytilde = np.concatenate((measurements, np.zeros((operatorsize-signalsize, measurements.shape[1]))))

        realcosupport = realdict['cosupport']
        realsupport = np.zeros((operator.shape[0] - realcosupport.shape[0], realcosupport.shape[1]), dtype=int)
        for i in range(realcosupport.shape[1]):
            realsupport[:, i] = np.setdiff1d(list(range(operator.shape[0])), realcosupport[:, i])

        datatilde = np.concatenate((realdict['data'], np.zeros((operatorsize-signalsize, realdict['data'].shape[1]))))
        realdict_synth = {'data': datatilde, 'gamma': realdict['gamma'], 'support': realsupport}

        return np.dot(dictionary, self.synthsolver.solve(ytilde, Atilde, realdict_synth))

    def compute_multiplier(self, measurements, acqumatrix, operator):
        """
        Computes the value of the nullspace multipler

        :param measurements: Measurements matrix
        :param acqumatrix: Acquisition matrix
        :param operator: Operator
        :return: Value of the multiplier
        """

        if self.nullspace_multiplier_type == "value":
            mul = self.nullspace_multiplier
        elif self.nullspace_multiplier_type == "normalized_row":
            operatorsize, signalsize = operator.shape
            # Find nullspace
            dictionary = np.linalg.pinv(operator)
            U,S,Vt = np.linalg.svd(dictionary)
            nullspace = Vt[-(operatorsize-signalsize):, :]

            mul = self.nullspace_multiplier / np.linalg.norm(nullspace, 'fro') * nullspace.shape[0] * np.linalg.norm(np.dot(acqumatrix, dictionary), 'fro') / acqumatrix.shape[0]

        return mul

