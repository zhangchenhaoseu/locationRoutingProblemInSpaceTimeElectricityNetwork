import pandas as pd
import numpy as np
import math
import time
from gurobipy import *

start = time.time()
T = 9
E = 5
N = 9
station1 = 1  # construct cost
B = 1
cap1 = 2



edge_data = np.loadtxt(open("Edges.csv", "rb"), delimiter=",", skiprows=1)

edge = []
node = []
for i in range(len(edge_data)):
    edge.append((edge_data[i][1], edge_data[i][2], edge_data[i][3], edge_data[i][4], edge_data[i][5], edge_data[i][6],
                 edge_data[i][7], edge_data[i][8], edge_data[i][9], edge_data[i][10], edge_data[i][11],
                 edge_data[i][12], edge_data[i][13]))  # start_id	end_id	edge_dis	V_time1	V_time2	V_time3

for id in range(1, N):
    for t in range(T + 1):
        for ele in range(E + 1):
            node.append((id, t, ele))
actnode = []
for id in range(1, N):
    actnode.append(id)
nodes = tuplelist(node)  # (space,time,electricity)
edge = tuplelist(edge)
t_list = []


def setT(Tk, n):
    for i in range(n):
        t_list.append((i * Tk / n, (i + 1) * Tk / n))

setT(T, 3)
T_list = tuplelist(t_list)

def getT(t):
    for i in range(len(T_list)):
        if T_list[i][0] <= t < T_list[i][1]:
            return i

def qv(v):
    if v == 1:
        return 1.5
    elif v == 2:
        return 1
    elif v == 3:
        return 1.5

est = []  # space-time-electricity arc

def newEdge(i, t, e):
    tempedge = edge.select(i, '*', '*', '*', '*', '*')
    # estedge=[]
    for realedge in tempedge:
        # D=realedge[2]
        dis = realedge[2]
        t_cost = 0
        e_cost = 0
        tempt = t
        nowt = 0
        if t >= T:
            break
        for j in range(len(t_list)):
            if t_list[j][0] <= tempt < t_list[j][1]:
                # v= realedge[j + 4]
                nowt = j
                break
        for k in range(nowt, len(T_list)):
            t_surplus = T_list[k][1] - tempt
            if dis <= 0:
                break
            if dis < t_surplus * realedge[k + 3]:
                t_cost = t_cost + dis / realedge[k + 3]
                e_cost = e_cost + dis * qv(realedge[k + 3])
                break
            else:
                t_cost = t_cost + t_surplus
                dis = dis - t_surplus * realedge[k + 3]
                e_cost = e_cost + t_surplus * realedge[k + 3] * qv(realedge[k + 3])
                tempt = T_list[k][1]
        if (t + t_cost <= T) and (e - e_cost >= 0):
            tempestedge = (
            i, t, e, math.ceil(realedge[1]), t + math.ceil(t_cost), e - math.ceil(e_cost), math.ceil(t_cost),
            math.ceil(e_cost))
            est.append(tempestedge)


for node in nodes:
    newEdge(node[0], node[1], node[2])

for node in nodes:
    if (node[1] + 1 <= T):
        if (node[2] + 1 <= E):
            est.append((node[0], node[1], node[2], node[0], node[1] + 1, min(node[2] + 2, E), 1,
                        (min(node[2] + 2, E)) - node[2]))

for node in nodes:
    if (node[1] + 1 <= T):
        est.append((node[0], node[1], node[2], node[0], node[1] + 1, node[2], 1, 0))

O_data = np.loadtxt(open("O.csv", "rb"), delimiter=",", skiprows=1)
D_data = np.loadtxt(open("D.csv", "rb"), delimiter=",", skiprows=1)
O = []
D = []
for i in range(len(O_data)):
    O.append((int(O_data[i][0]), int(O_data[i][1]), O_data[i][2], O_data[i][3]))  # (nodeO_index,supply,time_sensitivity,electricity_sensitivity)
for i in range(len(D_data)):
    D.append((int(D_data[i][0]), int(D_data[i][1]), int(D_data[i][2]), int(D_data[i][3])))  # (nodeD_index,demand,timewindowLeft,timewindowRight)

p = 2


try:
    RS_master = Model('Benders master-RS NET')

    Y = {Nod: RS_master.addVar(lb=0, vtype=GRB.BINARY, name='y_%s' % (Nod)) for Nod in actnode}

    z = RS_master.addVar(lb=0, vtype=GRB.CONTINUOUS, name='z')

    Y_key = list(Y.keys())
    expr1 = LinExpr()
    for y in Y_key:
        # # if y not in YR:
        #     RS_master.addLConstr(Y[y], GRB.EQUAL, 0)
        expr1.addTerms(station1, Y[y])
    RS_master.addLConstr(expr1, GRB.EQUAL, B)

    # 目标函数
    expr = LinExpr()
    expr.addTerms(1, z)
    RS_master.setObjective(expr, sense=GRB.MINIMIZE)

    RS_master.update()
    RS_master.Params.OutputFlag = 0
    RS_master.Params.DualReductions = 0
    # RS_master.write("RS_master.lp")

    RS_master.optimize()

    print(RS_master.status)
    print('\n\n\n')
    yVal = RS_master.getAttr('x', Y)
    print('Obj:', RS_master.ObjVal)
    ry = [0] * (N)
    for id in range(1, N):
        ry[id] = Y[id].x
    print('z:', z.x)


except GurobiError as ee:
    print("Error code" + str(ee.errno) + ": " + str(ee))
except AttributeError:
    print('Encountered an attribute error')

gap = 10000
it = 0

LB = -100000
UB = +100000

while gap > 0.02:
    it = it + 1

    print('**************************Iteration:', it)
    """ update SP by y_var """
    RS_sub = Model('Benders sub-RS NET')

    constrMu = {}
    constrNu = {}
    obj = LinExpr()
    nodeflowdin = [[[0 for _ in range(E + 1)] for _ in range(T + 1)] for _ in range(2 * N + 1)]
    X = {}
    idt = [[0 for _ in range(T + 1)] for _ in range(N)]
    for i in O:
        for t in range(T + 1):
            est.append((-i[0], 0, 0, i[0], t, E, 0, 0))
    for i in D:
        for t in range(T + 1):
            if i[2] <= t <= i[3]:
                for e in range(E + 1):
                    est.append((i[0], t, e, N + i[0], 0, 0, 0, 0))
    for i in O:
        for j in D:
            est.append((-i[0], 0, 0, N + j[0], 0, 0, 20, 20))

    for i in O:
        w1 = i[2]
        w2 = i[3]
        exprIout = LinExpr()
        nodeflowink = [[[0 for _ in range(E + 1)] for _ in range(T + 1)] for _ in range(2 * N + 1)]
        nodeflowoutk = [[[0 for _ in range(E + 1)] for _ in range(T + 1)] for _ in range(2 * N + 1)]
        expr0 = LinExpr()
        expr1 = LinExpr()
        for Edg in est:
            X[((Edg), i)] = RS_sub.addVar(lb=0, vtype=GRB.CONTINUOUS, name='x_%s_%s_%s_%s_%s_%s_%s_%s_(%s)' % (
                Edg[0], Edg[1], Edg[2], Edg[3], Edg[4], Edg[5], Edg[6], Edg[7], i[0]))

            if Edg[0] == -i[0]:
                nodeflowink[Edg[3]][Edg[4]][Edg[5]] += X[((Edg), i)]
                exprIout += X[((Edg), i)]
                if Edg[3] > N:
                    nodeflowdin[Edg[3]][0][0] += X[((Edg), i)]

            else:
                nodeflowink[Edg[3]][Edg[4]][Edg[5]] += X[((Edg), i)]
                nodeflowoutk[Edg[0]][Edg[1]][Edg[2]] += X[((Edg), i)]

            if Edg[3] > N and Edg[0] > 0:
                nodeflowdin[Edg[3]][0][0] += X[((Edg), i)]

            if (Edg[0] == Edg[3]) and (Edg[2] != Edg[5]):
                idt[Edg[0]][Edg[1]] += X[((Edg), i)]
                # if (Edg[0] not in YR):
                #     RS_sub.addLConstr(X[((Edg), i)], GRB.EQUAL, 0)

            obj += Edg[6] * X[((Edg), i)] * w1
            if Edg[0] != Edg[3]:
                obj += Edg[7] * X[((Edg), i)] * w2

        constrMu[i] = RS_sub.addLConstr(exprIout, GRB.EQUAL, i[1], name='O_%s_outflow' % (i[0]))
        RS_sub.update()
        for node in nodes:
            expr3 = nodeflowink[node[0]][node[1]][node[2]] - nodeflowoutk[node[0]][node[1]][node[2]]
            RS_sub.addLConstr(expr3, GRB.EQUAL, 0, name='%s_%s_%s_flow_balance' % (node[0], node[1], node[2]))
            RS_sub.update()

    for i in D:
        expr5 = nodeflowdin[i[0] + N][0][0]
        constrMu[i[0] + N] = RS_sub.addLConstr(expr5, GRB.EQUAL, i[1], name='D_%s_inflow' % i[0])
    RS_sub.update()
    for id in actnode:
        for t in range(T + 1):
            constrNu[id, t] = RS_sub.addLConstr(idt[id][t], GRB.LESS_EQUAL, cap1 * ry[id])

    RS_sub.setObjective(obj, sense=GRB.MINIMIZE)

    RS_sub.update()
    RS_sub.Params.OutputFlag = 0
    RS_sub.Params.InfUnbdInfo = 1
    RS_sub.Params.DualReductions = 0
    RS_sub.write("RS_sub.lp")
    RS_sub.optimize()
    print(RS_sub.status)

    """ update global UB """
    if RS_sub.status == 2:
        expr = RS_sub.ObjVal
        UB = min(UB, expr)
    """ generate Cuts """
    if RS_sub.status == 2:

        expr = 0
        for i in O:
            expr = expr + constrMu[i].pi * i[1]
        for j in D:
            expr = expr + constrMu[j[0] + N].pi * j[1]

        for id in actnode:
            for t in range(T + 1):

                expr = expr + constrNu[id, t].pi * Y[id] * cap1
        RS_master.addLConstr(expr, GRB.LESS_EQUAL, z, name='optimality cut_{}'.format(it))
    else:

        expr = 0
        for i in O:
            expr = expr - constrMu[i].FarkasDual * i[1]
        for j in D:
            expr = expr - constrMu[j[0] + N].FarkasDual * j[1]

        for id in actnode:
            for t in range(T):
                expr = expr - constrNu[id, t].FarkasDual * Y[id] * cap1
        RS_master.addLConstr(expr, GRB.LESS_EQUAL, 0, name='feasibal_cut_{}'.format(it))
    RS_master.update()
    RS_master.Params.OutputFlag = 0
    RS_master.Params.DualReductions = 0
    RS_master.write("RS_master.lp")

    RS_master.optimize()

    """ update the global LB """
    LB = max(LB, RS_master.ObjVal)
    """ update optimality Gap """
    print('UB:', UB, "LB:", LB)
    gap = abs(UB - LB)

    """ update y_bar"""
    yVal = RS_master.getAttr('x', Y)
    # y_bar_change.append(yVal)
    y_var = {}
    for id in range(1, N):
        ry[id] = Y[id].x
    print(yVal)
