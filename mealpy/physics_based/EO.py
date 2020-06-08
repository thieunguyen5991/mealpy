#!/usr/bin/env python
# ------------------------------------------------------------------------------------------------------%
# Created by "Thieu Nguyen" at 07:03, 18/03/2020                                                        %
#                                                                                                       %
#       Email:      nguyenthieu2102@gmail.com                                                           %
#       Homepage:   https://www.researchgate.net/profile/Thieu_Nguyen6                                  %
#       Github:     https://github.com/thieunguyen5991                                                  %
#-------------------------------------------------------------------------------------------------------%

from numpy import exp, sign, ones, mean
from numpy.random import uniform, randint
from copy import deepcopy
from mealpy.root import Root


class BaseEO(Root):
    """
        The original version of: Equilibrium Optimizer (EO)
            (Equilibrium Optimizer: A Novel Optimization Algorithm)
        Link:
            https://doi.org/10.1016/j.knosys.2019.105190
            https://www.mathworks.com/matlabcentral/fileexchange/73352-equilibrium-optimizer-eo
    """

    def __init__(self, obj_func=None, lb=None, ub=None, problem_size=50, batch_size=10, verbose=True, epoch=750, pop_size=100):
        Root.__init__(self, obj_func, lb, ub, problem_size, batch_size, verbose)
        self.epoch = epoch
        self.pop_size = pop_size
        self.V = 1
        self.a1 = 2
        self.a2 = 1
        self.GP = 0.5

    def train(self):

        #c_eq1 = [None, float("inf")]                    # it is global best position
        c_eq2 = [None, float("inf")]
        c_eq3 = [None, float("inf")]
        c_eq4 = [None, float("inf")]

        # ---------------- Memory saving-------------------
        pop = [self.create_solution() for _ in range(self.pop_size)]
        g_best = self.get_global_best_solution(pop, self.ID_FIT, self.ID_MIN_PROB)
        c_eq1 = deepcopy(g_best)

        for epoch in range(0, self.epoch):

            for i in range(0, self.pop_size):

                if pop[i][self.ID_FIT] < c_eq1[self.ID_FIT]:
                    c_eq1 = deepcopy(pop[i])
                elif c_eq1[self.ID_FIT] < pop[i][self.ID_FIT] < c_eq2[self.ID_FIT]:
                    c_eq2 = deepcopy(pop[i])
                elif c_eq1[self.ID_FIT] < pop[i][self.ID_FIT] and c_eq2[self.ID_FIT] < pop[i][self.ID_FIT] < c_eq3[self.ID_FIT]:
                    c_eq3 = deepcopy(pop[i])
                elif c_eq1[self.ID_FIT] < pop[i][self.ID_FIT] and c_eq2[self.ID_FIT] < pop[i][self.ID_FIT] and c_eq3[self.ID_FIT] < pop[i][self.ID_FIT] < c_eq4[self.ID_FIT]:
                    c_eq4 = deepcopy(pop[i])

            # make equilibrium pool
            c_eq_ave = (c_eq1[self.ID_POS] + c_eq2[self.ID_POS] + c_eq3[self.ID_POS] + c_eq4[self.ID_POS]) / 4
            fit_ave = self.get_fitness_position(c_eq_ave)
            c_pool = [c_eq1, c_eq2, c_eq3, c_eq4, [c_eq_ave, fit_ave]]

            # Eq. 9
            t = (1 - epoch/self.epoch) ** (self.a2 * epoch / self.epoch)

            for i in range(0, self.pop_size):
                lamda = uniform(0, 1, self.problem_size)                # lambda in Eq. 11
                r = uniform(0, 1, self.problem_size)                    # r in Eq. 11
                c_eq = c_pool[randint(0, len(c_pool))][self.ID_POS]     # random selection 1 of candidate from the pool
                f = self.a1 * sign(r - 0.5) * (exp(-lamda * t) - 1.0)        # Eq. 11
                r1 = uniform()
                r2 = uniform()                                                                  # r1, r2 in Eq. 15
                gcp = 0.5 * r1 * ones(self.problem_size) * (r2 >= self.GP)                           # Eq. 15
                g0 = gcp * (c_eq - lamda * pop[i][self.ID_POS])                                 # Eq. 14
                g = g0 * f                                                                      # Eq. 13
                temp = c_eq + (pop[i][self.ID_POS] - c_eq) * f + (g * self.V / lamda) * (1.0 - f)    # Eq. 16
                fit = self.get_fitness_position(temp)
                pop[i] = [temp, fit]

            g_best = self.update_global_best_solution(pop, self.ID_MIN_PROB, g_best)
            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train


class LevyEO(BaseEO):
    """
        My modified version of: Equilibrium Optimizer (EO)
    """

    def __init__(self, obj_func=None, lb=None, ub=None, problem_size=50, batch_size=10, verbose=True, epoch=750, pop_size=100):
        BaseEO.__init__(self, obj_func, lb, ub, problem_size, batch_size, verbose, epoch, pop_size)

    def _make_equilibrium_pool__(self, list_equilibrium=None):
        pos_list = [item[self.ID_POS] for item in list_equilibrium]
        pos_mean = mean(pos_list, axis=0)
        fit = self.get_fitness_position(pos_mean)
        list_equilibrium.append([pos_mean, fit])
        return list_equilibrium

    def train(self):
        # Initialization
        pop = [self.create_solution() for _ in range(self.pop_size)]

        # ---------------- Memory saving-------------------
        # make equilibrium pool
        pop_sorted = sorted(pop, key=lambda item: item[self.ID_FIT])
        c_eq_list = deepcopy(pop_sorted[:4])
        g_best = deepcopy(c_eq_list[0])
        c_pool = self._make_equilibrium_pool__(c_eq_list)

        for epoch in range(0, self.epoch):
            # Eq. 9
            t = (1 - epoch / self.epoch) ** (self.a2 * epoch / self.epoch)

            for i in range(0, self.pop_size):
                if uniform() < 0.5:
                    lamda = uniform(0, 1, self.problem_size)  # lambda in Eq. 11
                    r = uniform(0, 1, self.problem_size)  # r in Eq. 11
                    c_eq = c_pool[randint(0, len(c_pool))][self.ID_POS]  # random selection 1 of candidate from the pool
                    f = self.a1 * sign(r - 0.5) * (exp(-lamda * t) - 1.0)  # Eq. 11
                    r1 = uniform()
                    r2 = uniform()  # r1, r2 in Eq. 15
                    gcp = 0.5 * r1 * ones(self.problem_size) * (r2 >= self.GP)  # Eq. 15
                    g0 = gcp * (c_eq - lamda * pop[i][self.ID_POS])  # Eq. 14
                    g = g0 * f  # Eq. 13
                    temp = c_eq + (pop[i][self.ID_POS] - c_eq) * f + (g * self.V / lamda) * (1.0 - f)  # Eq. 16
                else:
                    ## Idea: Sometimes, an unpredictable event happens, It make the status of equilibrium change.
                    temp = self.levy_flight(epoch, pop[i][self.ID_POS], g_best[self.ID_POS])
                fit = self.get_fitness_position(temp)
                pop[i] = [temp, fit]

            # Update the equilibrium pool
            pop_sorted = deepcopy(pop)
            pop_sorted = pop_sorted + c_pool
            pop_sorted = sorted(pop_sorted, key=lambda item: item[self.ID_FIT])
            c_eq_list = deepcopy(pop_sorted[:4])
            c_pool = self._make_equilibrium_pool__(c_eq_list)

            if pop_sorted[0][self.ID_FIT] < g_best[self.ID_FIT]:
                g_best = deepcopy(pop_sorted[0])
            self.loss_train.append(g_best[self.ID_FIT])
            if self.verbose:
                print(">Epoch: {}, Best fit: {}".format(epoch + 1, g_best[self.ID_FIT]))
        self.solution = g_best
        return g_best[self.ID_POS], g_best[self.ID_FIT], self.loss_train
