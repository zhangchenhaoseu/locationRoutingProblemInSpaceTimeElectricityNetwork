from gurobipy import *
import pandas as pd
import time


"""——————————————The shortest path time problem, the waiting arc cost at the start and end points is set to 0——————————————"""
def modelingAndSolve(STEarcpath,STEnodepath):
    m = Model('LRP')
    arcDataDf = pd.read_csv(STEarcpath)
    nodeDataDf = pd.read_csv(STEnodepath)
    depots = [0, 1, 2]
    customers = [5, 6, 7]
    supply = [1, 3, 1]
    demand = [2, 1, 2]
    L = [i for i in range(0,len(depots))]
    electricityList = [0,1,2,3,4,5,6,7,8]
    timeList = [i for i in range(0,15)]
    nodeList = list(pd.unique(arcDataDf['from_space']))
    candidateCharging = [1,2,3,4,5,6]
    theata = 2

    X = [[[[[[[[] for _ in range(0,len(electricityList))] for _ in range(0,len(electricityList))] for _ in range(0,len(timeList))] for _ in range(0,len(timeList))] for _ in range(0,len(nodeList)+6)] for _ in range(0,len(nodeList)+6)] for _ in range(0,len(L))]  # x_lijtt'ee'
    Y = [[] for _ in range(0,len(candidateCharging))]

    for l in L:
        for _index in range(0,len(arcDataDf)):
            i = arcDataDf.loc[_index,"from_space"]
            j = arcDataDf.loc[_index,"to_space"]
            t = arcDataDf.loc[_index,"from_time"]
            t_ = arcDataDf.loc[_index,"to_time"]
            e = arcDataDf.loc[_index,"from_electricity"]
            e_ = arcDataDf.loc[_index,"to_electricity"]
            # print(f"X_{l}_{i}_{j}_{t}_{t_}_{e}_{e_}")
            X[l][i][j][t][t_][e][e_] = m.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"X_{l}_{i}_{j}_{t}_{t_}_{e}_{e_}")
    for _index in range(0,len(candidateCharging)):
        Y[_index] = m.addVar(lb=0,vtype=GRB.BINARY, name=f"Y_{_index}")

    m.update()

    obj = LinExpr(0)
    cnt = 0
    for l in L:
        for _index in range(0,len(arcDataDf)):
            i = arcDataDf.loc[_index,"from_space"]
            j = arcDataDf.loc[_index,"to_space"]
            t = arcDataDf.loc[_index,"from_time"]
            t_ = arcDataDf.loc[_index,"to_time"]
            e = arcDataDf.loc[_index,"from_electricity"]
            e_ = arcDataDf.loc[_index,"to_electricity"]
            timeCost = arcDataDf.loc[_index,"timeCost"]
            electricityCost = arcDataDf.loc[_index,"electricityCost"]
            obj.addTerms(timeCost+electricityCost, X[l][i][j][t][t_][e][e_])
            cnt+=1
    m.setObjective(obj, sense=GRB.MINIMIZE)
    # Starting point outflow constraint
    num = 0
    for l in L:
        expr = LinExpr(0)
        for _index in range(0,len(arcDataDf)):
            i = arcDataDf.loc[_index,"from_space"]
            j = arcDataDf.loc[_index,"to_space"]
            t = arcDataDf.loc[_index,"from_time"]
            t_ = arcDataDf.loc[_index,"to_time"]
            e = arcDataDf.loc[_index,"from_electricity"]
            e_ = arcDataDf.loc[_index,"to_electricity"]
            if i == l+8:
                expr.addTerms(1,X[l][i][j][t][t_][e][e_])
        num += 1
        m.addConstr(expr == supply[l], f'C1_{l}')

    # End point inflow constraints
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
                if i == k+6:
                    expr.addTerms(1, X[l][j][i][t_][t][e_][e])
        num += 1
        m.addConstr(expr == demand[k_index], f'C2_{k}')

    # Intermediate node flow balance
    for l in L:
        for _ in range(0,len(nodeDataDf)):
            print(_/len(nodeDataDf))
            node_i = nodeDataDf.loc[_,"space"]
            node_t = nodeDataDf.loc[_,"time"]
            node_e = nodeDataDf.loc[_,"electricity"]
            expr1 = LinExpr(0)
            expr2 = LinExpr(0)
            for _index in range(0,len(arcDataDf)):
                i = arcDataDf.loc[_index, "from_space"]
                j = arcDataDf.loc[_index, "to_space"]
                t = arcDataDf.loc[_index, "from_time"]
                t_ = arcDataDf.loc[_index, "to_time"]
                e = arcDataDf.loc[_index, "from_electricity"]
                e_ = arcDataDf.loc[_index, "to_electricity"]
                if (i,t,e) == (node_i,node_t,node_e):
                    expr1.addTerms(1,X[l][i][j][t][t_][e][e_])
            for _index in range(0,len(arcDataDf)):
                j = arcDataDf.loc[_index, "from_space"]
                i = arcDataDf.loc[_index, "to_space"]
                t_ = arcDataDf.loc[_index, "from_time"]
                t = arcDataDf.loc[_index, "to_time"]
                e_ = arcDataDf.loc[_index, "from_electricity"]
                e = arcDataDf.loc[_index, "to_electricity"]
                if (i,t,e) == (node_i,node_t,node_e):
                    expr2.addTerms(1,X[l][j][i][t_][t][e_][e])
            m.addConstr(expr1-expr2 == 0, f'C3_{l,node_i,node_t,node_e}')
            num += 1
            # print(num)

    # Capacity Constraints
    for i_index in range(0,len(candidateCharging)):
        for t_name in timeList:
            expr = LinExpr(0)
            for l in L:
                for _index in range(0,len(arcDataDf)):
                    i = arcDataDf.loc[_index, "from_space"]
                    j = arcDataDf.loc[_index, "to_space"]
                    t = arcDataDf.loc[_index, "from_time"]
                    t_ = arcDataDf.loc[_index, "to_time"]
                    e = arcDataDf.loc[_index, "from_electricity"]
                    e_ = arcDataDf.loc[_index, "to_electricity"]
                    if (i,t) == (candidateCharging[i_index],t_name):
                        if e < e_:
                            if i <=7 and j<=7:
                                expr.addTerms(1,X[l][i][i][t][t_][e][e_])
            m.addConstr(expr <= theata*Y[i_index], f'C4_{candidateCharging[i_index],t_name}')
            num += 1

    # Budget Constraints
    expr = LinExpr(0)
    for i_index in range(0,len(candidateCharging)):
        expr.addTerms(1,Y[i_index])
    m.addConstr(expr <= 2, f'C5_{0}')

    m.write('LRP.lp')
    m.optimize()
    if m.status == GRB.OPTIMAL:
        print("-" * 20, "Solved successfully", '-' * 20)
        print(f"The objective value is: {m.ObjVal}")
    else:
        print("No solution")
    # Display the solution results
    var_lst = m.getVars()
    # print('var_lst:')
    for i in var_lst:
        if round(i.x, 6) != 0:
            print(i)
    return m


if __name__ == "__main__":
    STEarcpath = r'STE_arc.txt'
    STEnodepath = r'STE_node.txt'
    startTime = time.time()
    modelingAndSolve(STEarcpath,STEnodepath)
    endTime = time.time()
    print("time：",endTime-startTime)