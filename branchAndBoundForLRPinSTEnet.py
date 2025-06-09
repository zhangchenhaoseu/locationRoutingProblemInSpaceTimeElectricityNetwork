from gurobipy import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import copy
import time


''' --------------------Step 1, use guroubi to establish the linear relaxation problem (IPr) of (IP)-------------------- '''
def modeling(STEarcpath,STEnodepath):
    m = Model('IPr')
    arcDataDf = pd.read_csv(STEarcpath)
    nodeDataDf = pd.read_csv(STEnodepath)
    depots = [0, 1, 2]
    customers = [5, 6, 7]
    supply = [1, 3, 1]
    demand = [2, 1, 2]
    L = [i for i in range(0, len(depots))]
    electricityList = [0, 1, 2, 3, 4]
    timeList = [i for i in range(0, 10)]
    nodeList = list(pd.unique(arcDataDf['from_space']))
    candidateCharging = [1, 2, 3, 4, 5, 6]
    theata = 2

    X = [[[[[[[[] for _ in range(0, len(electricityList))] for _ in range(0, len(electricityList))] for _ in
             range(0, len(timeList))] for _ in range(0, len(timeList))] for _ in range(0, len(nodeList) + 6)] for _ in
          range(0, len(nodeList) + 6)] for _ in range(0, len(L))]  # x_lijtt'ee'
    Y = [[] for _ in range(0, len(candidateCharging))]

    for l in L:
        for _index in range(0, len(arcDataDf)):
            i = arcDataDf.loc[_index, "from_space"]
            j = arcDataDf.loc[_index, "to_space"]
            t = arcDataDf.loc[_index, "from_time"]
            t_ = arcDataDf.loc[_index, "to_time"]
            e = arcDataDf.loc[_index, "from_electricity"]
            e_ = arcDataDf.loc[_index, "to_electricity"]
            # print(f"X_{l}_{i}_{j}_{t}_{t_}_{e}_{e_}")
            X[l][i][j][t][t_][e][e_] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"X_{l}_{i}_{j}_{t}_{t_}_{e}_{e_}")
    for _index in range(0, len(candidateCharging)):
        Y[_index] = m.addVar(lb=0,ub=1, vtype=GRB.CONTINUOUS, name=f"Y_{_index}")
    m.update()

    obj = LinExpr(0)
    cnt = 0
    for l in L:
        for _index in range(0, len(arcDataDf)):
            i = arcDataDf.loc[_index, "from_space"]
            j = arcDataDf.loc[_index, "to_space"]
            t = arcDataDf.loc[_index, "from_time"]
            t_ = arcDataDf.loc[_index, "to_time"]
            e = arcDataDf.loc[_index, "from_electricity"]
            e_ = arcDataDf.loc[_index, "to_electricity"]
            timeCost = arcDataDf.loc[_index, "timeCost"]
            electricityCost = arcDataDf.loc[_index, "electricityCost"]
            obj.addTerms(timeCost + electricityCost, X[l][i][j][t][t_][e][e_])
            cnt += 1
    m.setObjective(obj, sense=GRB.MINIMIZE)

    # Starting point outflow constraint
    num = 0
    for l in L:
        expr = LinExpr(0)
        for _index in range(0, len(arcDataDf)):
            i = arcDataDf.loc[_index, "from_space"]
            j = arcDataDf.loc[_index, "to_space"]
            t = arcDataDf.loc[_index, "from_time"]
            t_ = arcDataDf.loc[_index, "to_time"]
            e = arcDataDf.loc[_index, "from_electricity"]
            e_ = arcDataDf.loc[_index, "to_electricity"]
            if i == l + 8:
                expr.addTerms(1, X[l][i][j][t][t_][e][e_])
        num += 1
        m.addConstr(expr == supply[l], f'C1_{l}')

    # End point inflow constraint
    num = 0
    for k in customers:
        k_index = customers.index(k)
        expr = LinExpr(0)
        for l in L:
            for _index in range(0, len(arcDataDf)):
                j = arcDataDf.loc[_index, "from_space"]
                i = arcDataDf.loc[_index, "to_space"]
                t_ = arcDataDf.loc[_index, "from_time"]
                t = arcDataDf.loc[_index, "to_time"]
                e_ = arcDataDf.loc[_index, "from_electricity"]
                e = arcDataDf.loc[_index, "to_electricity"]
                if i == k + 6:
                    expr.addTerms(1, X[l][j][i][t_][t][e_][e])
        num += 1
        m.addConstr(expr == demand[k_index], f'C2_{k}')

    # Intermediate node flow balance
    for l in L:
        for _ in range(0, len(nodeDataDf)):
            # print(_ / len(nodeDataDf))
            node_i = nodeDataDf.loc[_, "space"]
            node_t = nodeDataDf.loc[_, "time"]
            node_e = nodeDataDf.loc[_, "electricity"]
            expr1 = LinExpr(0)
            expr2 = LinExpr(0)
            for _index in range(0, len(arcDataDf)):
                i = arcDataDf.loc[_index, "from_space"]
                j = arcDataDf.loc[_index, "to_space"]
                t = arcDataDf.loc[_index, "from_time"]
                t_ = arcDataDf.loc[_index, "to_time"]
                e = arcDataDf.loc[_index, "from_electricity"]
                e_ = arcDataDf.loc[_index, "to_electricity"]
                if (i, t, e) == (node_i, node_t, node_e):
                    expr1.addTerms(1, X[l][i][j][t][t_][e][e_])
            for _index in range(0, len(arcDataDf)):
                j = arcDataDf.loc[_index, "from_space"]
                i = arcDataDf.loc[_index, "to_space"]
                t_ = arcDataDf.loc[_index, "from_time"]
                t = arcDataDf.loc[_index, "to_time"]
                e_ = arcDataDf.loc[_index, "from_electricity"]
                e = arcDataDf.loc[_index, "to_electricity"]
                if (i, t, e) == (node_i, node_t, node_e):
                    expr2.addTerms(1, X[l][j][i][t_][t][e_][e])
            m.addConstr(expr1 - expr2 == 0, f'C3_{l, node_i, node_t, node_e}')
            num += 1
            # print(num)

    # Capacity Constraints
    for i_index in range(0, len(candidateCharging)):
        for t_name in timeList:
            expr = LinExpr(0)
            for l in L:
                for _index in range(0, len(arcDataDf)):
                    i = arcDataDf.loc[_index, "from_space"]
                    j = arcDataDf.loc[_index, "to_space"]
                    t = arcDataDf.loc[_index, "from_time"]
                    t_ = arcDataDf.loc[_index, "to_time"]
                    e = arcDataDf.loc[_index, "from_electricity"]
                    e_ = arcDataDf.loc[_index, "to_electricity"]
                    if (i, t) == (candidateCharging[i_index], t_name):
                        if e < e_:
                            if i <= 7 and j <= 7:
                                expr.addTerms(1, X[l][i][i][t][t_][e][e_])
            m.addConstr(expr <= theata * Y[i_index], f'C4_{candidateCharging[i_index], t_name}')
            num += 1

    # Budget Constraints
    expr = LinExpr(0)
    for i_index in range(0, len(candidateCharging)):
        expr.addTerms(1, Y[i_index])
    m.addConstr(expr <= 2, f'C5_{0}')
    return m


''' --------------------Step 2: Create a node class to facilitate the use of relevant information of the corresponding node in branch and bound-------------------- '''
class Node():
    def __init__(self):
        self.model = None
        self.local_UB = np.inf
        self.local_LB = 0
        self.y_sol = {}
        self.int_y_sol = {}
        self.is_integer = False
        self.branch_var_lst = []
        self.cnt = None

# Define class methods and deep copy (to facilitate the establishment of branched sub-problems based on the original nodes)
    def deepcopy(node):
        new_node = Node()
        new_node.model = node.model.copy()
        new_node.local_UB = np.inf
        new_node.local_LB = 0
        new_node.y_sol = copy.deepcopy(node.y_sol)
        new_node.int_y_sol = copy.deepcopy(node.int_y_sol)
        new_node.is_integer = node.is_integer
        new_node.branch_var_lst = []
        new_node.cnt = node.cnt
        return new_node


''' --------------------Step 3: Perform branch and bound------------------ '''
def BranchAndBound(IPr):
    IPr.optimize()
    global_UB = 100
    global_LB = IPr.ObjVal
    eps = 10**(-3)
    incumbent_node = Node()
    Gap = np.inf
    cnt = 0
    Queue = []
    global_UB_lst = [global_UB]
    global_LB_lst = [global_LB]

    """ ——————Step 3.2 Create the initial node—————— """
    node = Node()
    node.model = IPr.copy()
    node.local_UB = np.inf
    node.local_LB = IPr.ObjVal
    node.model.setParam('OutputFlag', 0)
    node.cnt = 0
    Queue.append(node)

    """ ——————Step 3.3 Branching loop—————— """
    while ((len(Queue) > 0) and (global_UB-global_LB > eps)):
        """ ——Step 3.3.1 Select a subproblem corresponding to a node in the queue and solve and determine its integer characteristics—— """
        current_node = Queue.pop()
        cnt += 1
        current_node.model.optimize()
        SolStatus = current_node.model.Status
        is_integer = True
        is_Pruned = False
        if SolStatus == 2:
            for var in current_node.model.getVars():
                if var.VarName.split("_")[0] == "Y":
                    print(var.VarName, '=', var.x)
                    current_node.y_sol[var.VarName] = var.x
                    if abs(var.x - int(var.x)) > eps:
                        is_integer = False
                        current_node.branch_var_lst.append(var.VarName)
                    else:
                        current_node.int_y_sol[var.VarName] = int(var.x)
            """ ——Step 3.3.2 Update local/global upper/lower bounds based on the solution value and its integer properties—— """
            if is_integer == True:
                current_node.is_integer = True
                current_node.local_UB = current_node.model.ObjVal
                current_node.local_LB = current_node.model.ObjVal
                if current_node.local_UB < global_UB:
                    incumbent_node = Node.deepcopy(current_node)
                global_UB = min(current_node.local_UB, global_UB)
            elif is_integer == False:
                current_node.is_integer = False
                current_node.local_UB = np.inf
                current_node.local_LB = current_node.model.ObjVal
            """ ——Step 3.3.3 Prune according to conditions—— """
            if is_integer == True:  # （1）Optimality Pruning
                is_Pruned = True
            if (is_integer == False) and (current_node.local_LB > global_UB):  # (2) Boundary pruning
                is_Pruned = True
            Gap = abs(round(100*(global_UB - global_LB)/global_LB,2))
            print(f" _____ {cnt} _____ Gap = {Gap}% _____ \n")
        else:  # The node does not have a feasible solution, so it is pruned.
            is_integer = False
            is_Pruned = True

        """ ——Step 3.3.4 Branching—— """
        if is_Pruned == False:
            branchVarName = current_node.branch_var_lst[0]
            distance_05 = abs(current_node.y_sol[branchVarName] - int(current_node.y_sol[branchVarName])-0.5)
            for var in current_node.branch_var_lst:
                distance_var = abs(current_node.y_sol[var] - int(current_node.y_sol[var])-0.5)
                if distance_var < distance_05:
                    branchVarName = var
                    distance_05 = distance_var
            left_bound = int(current_node.y_sol[branchVarName])
            right_bound = left_bound + 1
            left_node = Node.deepcopy(current_node)
            right_node = Node.deepcopy(current_node)
            targetVar = left_node.model.getVarByName(branchVarName)
            expr_left = targetVar <= left_bound
            left_node.model.addConstr(expr_left, name='branch left' + str(cnt))
            left_node.model.setParam('OutputFlag',0)
            left_node.model.update()
            cnt += 1
            left_node.cnt = cnt
            targetVar = right_node.model.getVarByName(branchVarName)
            expr_right = targetVar >= right_bound
            right_node.model.addConstr(expr_right, name='branch right' + str(cnt))
            right_node.model.setParam('OutputFlag', 0)
            right_node.model.update()
            cnt += 1
            right_node.cnt = cnt
            Queue.append(left_node)
            Queue.append(right_node)
            temp_global_LB = global_UB
            for node in Queue:
                node.model.optimize()
                if node.model.status==2:
                    if node.model.ObjVal <= temp_global_LB:
                        temp_global_LB = node.model.ObjVal
            global_LB = temp_global_LB
            global_UB_lst.append(global_UB)
            global_LB_lst.append(global_LB)

    global_UB = global_LB
    Gap = abs(round(100*(global_UB - global_LB)/global_LB,2))
    global_UB_lst.append(global_UB)
    global_LB_lst.append(global_LB)

    print('\n\n')
    print('----------------------------------------------')
    print('          Branch and Bound Terminates         ')
    print('            Optimal Solution Found            ')
    print('----------------------------------------------')
    print(f'\n Final Gap = {Gap}%')
    print(f'Optimal Solution: {incumbent_node.int_y_sol}')
    print(f'Optimal Object（LB）: {global_LB}')
    print(f'Optimal Object（UB）: {global_UB}')
    return incumbent_node, Gap, global_LB_lst, global_UB_lst

def plotSolution(global_LB_lst, global_UB_lst):
    plt.xlabel("Iteration")
    plt.ylabel("Value of Bound")
    x_cor = [i+1 for i in range(0, len(global_UB_lst))]
    plt.plot(x_cor, global_UB_lst, c='red', label='Upper bound')
    plt.plot(x_cor, global_LB_lst, c='blue', label='Lower bound')
    print(len(global_LB_lst))
    plt.grid(False)
    plt.legend(loc='best')
    plt.show()
    return 0


if __name__ =="__main__":
    STEarcpath = r'STE_arc.txt'
    STEnodepath = r'STE_node.txt'
    IPr = modeling(STEarcpath,STEnodepath)
    time_start = time.time()
    incumbent_node, Gap, global_LB_lst, global_UB_lst = BranchAndBound(IPr)
    time_end = time.time()
    plotSolution(global_LB_lst, global_UB_lst)