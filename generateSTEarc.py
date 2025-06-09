import pandas as pd


def generateStsArcForVehicle(depots,customers):
    readPath = r'link_ini.txt'
    savePath = r'STE_arc.txt'
    readDf = pd.read_csv(readPath)

    electricityList = [0,1,2,3,4]  # electricity set
    timeStampList = [i for i in range(0, 10)]  # research time horizon

    nodeList = list(pd.unique(readDf['from_node']))
    arcList = []
    for i in range(0,len(readDf)):
        arcList.append((readDf.loc[i,'from_node'],readDf.loc[i,'to_node']))
    arcList = list(set(arcList))
    candidateCharging = [1, 2, 3, 4, 5, 6]
    file = open(savePath, 'w').close()
    file_generate = open(savePath, mode='a')
    file_generate.write(str('from_space') + ","+str('to_space')+ "," +str('from_time')+ "," +str('to_time') + "," +str('from_electricity')+ "," +str('to_electricity')+","+str('timeCost')+","+str('electricityCost')+","+str('arc_type'))
    file_generate.write('\n')

    cnt=0
    # construct the transportation arc
    for e in electricityList:
        for arc in arcList:
            i = arc[0]  # the origin of arc
            j = arc[1]  # the destination of arc
            for t in timeStampList:
                index = readDf[(readDf['from_node']==i) & (readDf['to_node']== j)].index[0]
                T_i_j_t = readDf.loc[index, 'length']
                timeCost = T_i_j_t  # 运输弧成本
                electricityCost = T_i_j_t
                if t+T_i_j_t in timeStampList and e-T_i_j_t in electricityList:
                    if (i==j) or (t == t+T_i_j_t):  # for the arcs whose space and time remain unchanged
                        pass
                    else:
                        file_generate.write(str(i) + "," + str(j) + "," + str(t) + "," + str(t+T_i_j_t) + "," + str(e) + "," + str(e-T_i_j_t)+ "," + str(timeCost)+ "," + str(electricityCost)+ "," + str(0))
                        file_generate.write('\n')
                        cnt += 1
    print('the count of the transportation arcs:', cnt)

    # construct the waiting arc
    """note: shortest path time problem, thus the cost of waiting arcs of O/D is set to zero"""
    cnt=0
    for e in electricityList:
        for i in nodeList:
            for t in timeStampList:
                timeCost = 1  # unit waiting arc cost
                electricityCost = 0
                if t + timeCost in timeStampList:
                    file_generate.write(str(i) + "," + str(i) + "," + str(t) + "," + str(t + 1) + "," + str(e) + "," + str(e) + "," + str(timeCost)+ "," + str(electricityCost) + "," + str(1))
                    file_generate.write('\n')
                    cnt += 1
    print('the count of the waiting arcs:',cnt)

    # construct the charging arc
    cnt=0
    for i in candidateCharging:
        for t in timeStampList:
            for e in electricityList:
                chargingTime = 1
                chargingElec = 1
                if t + chargingTime in timeStampList and e+chargingElec in electricityList:
                    file_generate.write(str(i) + "," + str(i) + "," + str(t) + "," + str(t + chargingTime) + "," + str(e) + "," + str(e+chargingElec) + "," + str(chargingTime)+ "," + str(0)+","+str(2))
                    file_generate.write('\n')
                    cnt += 1
    print('the count of the charging arcs:',cnt)

    # construct the super origin and destination and its corresponding dummy arc
    cnt = 0
    for i in depots:
        for t in timeStampList:
            file_generate.write(str(i+8) + "," + str(i) + "," + str(0) + "," + str(t) + "," + str(max(electricityList)) + "," + str(max(electricityList)) + "," + str(0) + "," + str(0) + "," + str(3))
            file_generate.write('\n')
            cnt += 1
    for i in customers:
        for t in timeStampList:
            for e in electricityList:
                file_generate.write(str(i) + "," + str(i+6) + "," + str(t) + "," + str(0) + "," + str(e) + "," + str(max(electricityList)) + "," + str(0) + "," + str(0) + "," + str(3))
                file_generate.write('\n')
                cnt += 1
    for i in depots:
        for j in customers:
            file_generate.write(str(i+8) + "," + str(j+6) + "," + str(0) + "," + str(0) + "," + str(max(electricityList)) + "," + str(max(electricityList)) + "," + str(100) + "," + str(100) + "," + str(3))
            file_generate.write('\n')
            cnt += 1

    print('the count of the dummy arcs:',cnt)
    file_generate.close()


if __name__ == "__main__":
    depots = [0,1,2]
    customers = [5,6,7]
    generateStsArcForVehicle(depots, customers)